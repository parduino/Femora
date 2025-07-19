from __future__ import annotations

from typing import List
from collections import defaultdict

import numpy as np
import pyvista as pv

from femora.components.interface.interface_base import InterfaceBase
from femora.components.event.mixins import HandlesDecompositionMixin
from femora.components.Mesh.meshPartBase import MeshPart
from femora.components.Mesh.meshPartInstance import SingleLineMesh, StructuredLineMesh
from femora.components.event.event_bus import EventBus, FemoraEvent
from femora.components.interface.embedded_info import EmbeddedInfo




class EmbeddedBeamSolidInterface(InterfaceBase, HandlesDecompositionMixin):
    """Create an *embedded beam–solid* contact interface.

    Parameters
    ----------
    name : str
        Unique interface name.
    beam_part : str
        *user_name* of the **line** `MeshPart` containing beam elements.
    solid_part : str
        *user_name* of the **volume** `MeshPart` containing hexahedral elements.
    radius : float
        Cylinder radius used to pick surrounding solid cells.
    n_peri, n_long : int
        Discretisation for `generateInterfacePoints` TCL command.
    crd_transf_tag : int
        Tag of an existing coordinate-transformation in the model.
    penalty_param : float | None
        Overrides default 1.0e12.
    g_penalty : bool
        Whether to add the "-gPenalty" flag.
    """

    _embeddedinfo_list: List[EmbeddedInfo] = []  # Class-level list to store all instances
    # Guard to ensure we register the class-level callback only once
    _class_subscribed: bool = False

    def __init__(
        self,
        name: str,
        beam_part: 'MeshPart | str | int',
        radius: float,
        n_peri: int = 8,
        n_long: int = 10,
        crd_transf_tag: int | None = None,
        penalty_param: float = 1.0e12,
        g_penalty: bool = True,
    ) -> None:
        # Helper to resolve MeshPart from str, int, or instance
        def resolve_meshpart(mp):
            if isinstance(mp, MeshPart):
                return mp
            elif isinstance(mp, str):
                return MeshPart.get_mesh_parts().get(mp)
            elif isinstance(mp, int):
                for part in MeshPart.get_mesh_parts().values():
                    if getattr(part, 'tag', None) == mp:
                        return part
            return None

        resolved_beam = resolve_meshpart(beam_part)
        if resolved_beam is None:
            raise ValueError(f"Could not retrieve beam_part '{beam_part}' to a MeshPart.")
        # Enforce beam_part is SingleLineMesh
        if not isinstance(resolved_beam, (SingleLineMesh, StructuredLineMesh)):
            raise TypeError("beam_part must be a SingleLineMesh or StructuredLineMesh instance.")

        super().__init__(name=name, owners=[resolved_beam.user_name])

        # store references
        self.beam_part = resolved_beam
        self.radius = radius
        self.n_peri = n_peri
        self.n_long = n_long
        self.crd_transf_tag = crd_transf_tag
        self.penalty_param = penalty_param
        self.g_penalty = g_penalty



    def _fork_solid_for_single_beam(self, assembled_mesh: pv.UnstructuredGrid, beam_cells_idx: np.ndarray):
        """
        Fork solid mesh for a single beam element.

        This method is forking the solid mesh around single beam element
        to ensure that the solid mesh is consistent with the beam element's core.
        It will extract the solid cells that are within the radius of the beam element
        and edit the _core_elements dictionary to include the solid elements
        that are within the radius of the beam element.
        """
        assembled_mesh = assembled_mesh.copy()
        beam_core_array = assembled_mesh.cell_data["Core"][beam_cells_idx]
        unique_cores = np.unique(beam_core_array)
        if unique_cores.size > 1:
            print(f"[EmbeddedBeamSolidInterface:{self.name}] Multiple cores found for beam cells: {unique_cores}.")
            print("Moving all beam cells to the first core for consistency.")
            print("all beam cells are going to be moved to core", unique_cores[0])
            # Move all beam cells to same core (pick first) for safety
            target_core = int(unique_cores[0])
            for c in unique_cores[1:]:
                assembled_mesh.cell_data["Core"][beam_cells_idx[beam_core_array == c]] = target_core
        else:
            print(f"[EmbeddedBeamSolidInterface:{self.name}] Single core found for beam cells: {unique_cores[0]}.")
            print("all beam cells are in the same core, core:", unique_cores[0])
            target_core = int(unique_cores[0])


        # Beam cell centers
        beam_points = assembled_mesh.copy().extract_cells(beam_cells_idx).points


        # TODO: need to modify the height since the the tail and head 
        # are not necessarily are the first and last points
        # FIXME: this is a hacky way to get the height of the beam

        beam_tail = beam_points[0]  # Take the first point as tail
        beam_head = beam_points[-1]  # Take the last point as head
        beam_vector = beam_head - beam_tail
        height = np.linalg.norm(beam_vector)
        center = (beam_tail + beam_head) / 2
        beam_vector = beam_vector / height  # Normalize the vector
        clinder = pv.Cylinder(center=center, 
                              direction=beam_vector, 
                              radius=self.radius,
                              height=height,
                              resolution=100,
                              capping=True)  

        # clinder.plot(show_edges=True, opacity=1.0, line_width=2)
        clinder = clinder.clean(inplace=False)  # Clean the cylinder mesh

        assembled_mesh.compute_implicit_distance(
            surface=clinder, 
            inplace=True
        )

        
        inner_ind = assembled_mesh.point_data["implicit_distance"] <= 0



        inner = assembled_mesh.extract_points(
            ind=inner_ind,
            include_cells=True,
            adjacent_cells=True,
            progress_bar=False
        )



        beam_elements = inner.celltypes == pv.CellType.LINE
        solid_elements = inner.celltypes == pv.CellType.HEXAHEDRON
        beam_ind = inner.cell_data["vtkOriginalCellIds"][beam_elements]
        solid_ind = inner.cell_data["vtkOriginalCellIds"][solid_elements]


        # save the assembeled mesh indexes to the inner mesh
        inner.cell_data["mesh_ind"] = np.zeros(inner.n_cells, dtype=np.int32)
        inner.cell_data["mesh_ind"][solid_elements] = solid_ind
        inner.cell_data["mesh_ind"][beam_elements] = beam_ind


        # Do a for loop and in every iteration pop up the largest solid mesh from the inner mesh
        solid_mesh = inner.extract_cells(solid_elements, progress_bar=False)
        beam_mesh  = inner.extract_cells(beam_elements, progress_bar=False)
        beams_solids = []
        while solid_mesh.n_cells > 0:
            solid_mesh_largest = solid_mesh.extract_largest()
            surf = solid_mesh_largest.extract_surface()
            beam_mesh.compute_implicit_distance(surf,inplace=True)
            beams = beam_mesh.point_data["implicit_distance"] <= 0
            beams = beam_mesh.extract_points(beams, include_cells=True, adjacent_cells=True, progress_bar=False)

            if beams.n_cells < 1:
                if solid_mesh_largest.n_cells < 1:
                    raise ValueError("No beams and solids found in the solid mesh.")
                else:
                    raise ValueError("No beams found in the solid mesh, but solids are present. This is unexpected. \
                                     probably the beam mesh size is too small. please increase the number of points in the beam mesh.")
            else:
                if solid_mesh_largest.n_cells < 1:
                    raise ValueError("No solids found in the solid mesh, but beams are present. This is unexpected. contact the developers.")
                
            
            beams = beams.cell_data["mesh_ind"]
            solids = solid_mesh_largest.cell_data["mesh_ind"]

            if len(beams) > 0 and len(solids) > 0:
                beams_solids.append((beams, solids))

            # now remove the largset solid mesh from the solid_mesh
            solid_mesh = solid_mesh.extract_values(solid_mesh_largest.cell_data["mesh_ind"] , invert=True, scalars="mesh_ind")
      
        
        
        print("num cells:", assembled_mesh.n_cells)
        print("num points:", assembled_mesh.n_points)


        if len(beams_solids) == 0:
            return
        

        ef = EmbeddedInfo(beams=beam_ind,
                     core_number= target_core,
                     beams_solids=beams_solids)
        # add the embedded info to the class-level list
        self._embeddedinfo_list.append(ef)


        assembled_mesh.cell_data["Core"][inner.cell_data["mesh_ind"]] = target_core





    def _on_post_assemble(self, assembled_mesh: pv.UnstructuredGrid, **kwargs):
        """Locate beam & solid element tags; enforce same core."""

        # shout  out that this is a post-assemble hook is called
        print(f"[EmbeddedBeamSolidInterface:{self.name}] Post-assemble hook called.")

        # Collect beam cells indices & compute their mean location
        beam_cells_idx = np.where(assembled_mesh.cell_data["MeshTag_cell"] == self.beam_part.tag)[0]
        if beam_cells_idx.size == 0:
            raise ValueError("No beam elements found in assembled mesh for provided MeshPart")
        
        # if beam_part is SingleLineMesh or StructuredLineMesh do different handling
        if isinstance(self.beam_part, SingleLineMesh):
            print(f"[EmbeddedBeamSolidInterface:{self.name}] SingleLineMesh detected, forking solid mesh around beam.")
            self._fork_solid_for_single_beam(assembled_mesh, beam_cells_idx)
        elif isinstance(self.beam_part, StructuredLineMesh):
            print(f"[EmbeddedBeamSolidInterface:{self.name}] StructuredLineMesh not yet supported for solid forking.")
        else:
            raise TypeError("beam_part must be a SingleLineMesh or StructuredLineMesh instance.")



        

    # ------------------------------------------------------------------
    # Event subscription
    # ------------------------------------------------------------------
    def _subscribe_events(self):  # type: ignore[override]
        """Override default subscription so RESOLVE_CORE_CONFLICTS is handled once per class."""
        # Per-instance hooks we still want
        EventBus.subscribe(FemoraEvent.PRE_ASSEMBLE, self._on_pre_assemble)
        EventBus.subscribe(FemoraEvent.POST_ASSEMBLE, self._on_post_assemble)
        EventBus.subscribe(FemoraEvent.POST_EXPORT, self._on_post_export)

        # Register the collective callback only the first time a pile is created
        if not self.__class__._class_subscribed:
            EventBus.subscribe(
                FemoraEvent.RESOLVE_CORE_CONFLICTS,
                self.__class__._cls_resolve_core_conflicts,
            )
            self.__class__._class_subscribed = True

    @classmethod
    def _cls_resolve_core_conflicts(cls, assembled_mesh: pv.UnstructuredGrid, **kwargs):
        """Resolve core conflicts across *all* EmbeddedInfo objects collected during assembly.

        Steps:
        1. Remove exact duplicates (equal EmbeddedInfo) – keep one.
        2. Detect conflicts → raise error immediately.
        3. Treat "similar" pairs as friends and build transitive groups.
        4. For each group, set every solid cell’s Core to the **minimum** core_number
           found in that group.
        """

        if not cls._embeddedinfo_list:
            return  # nothing to do
        print("resolving core conflicts")
        # ----------------------------------------------------------
        # 1. Deduplicate identical EmbeddedInfo objects
        # ----------------------------------------------------------
        unique_infos: list[EmbeddedInfo] = []
        for info in cls._embeddedinfo_list:
            if all(info != u for u in unique_infos):
                unique_infos.append(info)

        infos = unique_infos
        n = len(infos)

        # ----------------------------------------------------------
        # 2–3. Build similarity graph & detect conflicts
        # ----------------------------------------------------------
        parent = list(range(n))  # union-find structure

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(i: int, j: int):
            pi, pj = find(i), find(j)
            if pi != pj:
                parent[pj] = pi

        for i in range(n):
            for j in range(i + 1, n):
                relation = infos[i].compare(infos[j])
                if relation == "conflict":
                    raise ValueError(
                        f"EmbeddedInfo conflict detected between {infos[i]} and {infos[j]}"
                    )
                elif relation == "similar":
                    union(i, j)
                # "equal" already handled via deduplication

        # ----------------------------------------------------------
        # 4. Apply lowest core number per connected component
        # ----------------------------------------------------------
        groups = defaultdict(list)  # root index → list[info index]
        for idx in range(n):
            groups[find(idx)].append(idx)

        for idx_list in groups.values():
            min_core = min(infos[i].core_number for i in idx_list)
            for i in idx_list:
                info = infos[i]
                for _beams, solids in info.beams_solids:
                    try:
                        assembled_mesh.cell_data["Core"][solids] = min_core
                    except Exception as exc:
                        print(
                            f"[EmbeddedBeamSolidInterface] Failed to set core for solids {solids}: {exc}"
                        )
                try:
                    assembled_mesh.cell_data["Core"][list(info.beams)] = min_core
                except Exception as exc:
                    print(f"[EmbeddedBeamSolidInterface] Failed to set core for beams {info.beams}: {exc}")

        # Clear list so subsequent assemblies start fresh
        cls._embeddedinfo_list.clear()

        print("end of resolve core conflicts")
        pl = pv.Plotter()
        pl.add_mesh(assembled_mesh, color='blue', scalars="Core", opacity=1.0, show_edges=True)
        pl.show()



    # Keep an instance-level no-op to avoid accidental per-instance registration elsewhere
    def _on_resolve_core_conflicts(self, **payload):
        pass

    def _on_pre_assemble(self, **payload):
        # clear the class-level list
        self._embeddedinfo_list.clear()




if __name__ == "__main__":
    """Quick demo – builds a cube soil mesh and a central pile, then creates
    the EmbeddedBeamSolidInterface and exports a TCL file named
    `embedded_demo.tcl`.  Run with `python concrete_embedded_beam_solid.py`.
    """
    import femora as fm
    from femora.components.transformation.transformation import GeometricTransformation3D
    from femora.components.section.section_base import SectionManager
    # Ensure section types (e.g., 'Elastic') are registered
    import femora.components.section.section_opensees

    # Clear previous global state (helpful when running repeatedly)
    # fm.material.clear_all_materials()
    # fm.element.clear_all_elements()
    # fm.meshPart.clear_all_mesh_parts()
    # fm.section.clear_all_sections()
    # fm.region.clear()
    # fm.assembler.clear_assembly_sections()

    # ------------------------------------------------------------------
    # 1. Create materials and elements
    # ------------------------------------------------------------------
    soil_mat = fm.material.create_material("nDMaterial", "ElasticIsotropic", user_name="Soil", E=30e6, nu=0.3, rho=2000)
    brick_ele = fm.element.create_element("stdBrick", ndof=3, material=soil_mat)

    # Beam – needs section + transformation
    sec_mgr = SectionManager()   
    beam_sec = sec_mgr.create_section("Elastic", user_name="PileSection", E=2e11, A=0.05, Iz=1e-4, Iy=1e-4)
    transf = GeometricTransformation3D("Linear", 0, 1, 0)  # Local y-axis as vecXZ
    beam_ele = fm.element.create_element("DispBeamColumn", ndof=6, section=beam_sec, transformation=transf)

    # ------------------------------------------------------------------
    # 2. Create mesh parts
    # ------------------------------------------------------------------
    dx = 0.25
    Nx = int((10 - (-10)) / dx)
    Ny = Nx
    Nz = int((0 - (-20)) / dx)

    soil_mp = fm.meshPart.create_mesh_part(
        "Volume mesh", "Uniform Rectangular Grid", user_name="soil_vol", element=brick_ele,
        region=None,
        **{ 'X Min': -10, 'X Max': 10, 'Y Min': -10, 'Y Max': 10, 'Z Min': -20, 'Z Max': 0,
           'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': Nz }
    )
    soil_mp2 = fm.meshPart.create_mesh_part(
        "Volume mesh", "Uniform Rectangular Grid", user_name="cap", element=brick_ele,
        region=None,
        **{ 'X Min': -5, 'X Max': 5, 'Y Min': -5, 'Y Max': 5, 'Z Min': 1, 'Z Max': 2,
           'Nx Cells': 10//0.25, 'Ny Cells': 10//0.25, 'Nz Cells': 1//0.25 }
    )


    pile1 = fm.meshPart.create_mesh_part(
        "Line mesh", "Single Line", user_name="beam1", element=beam_ele,
        region=None,
        **{ 'x0': 0, 'y0': 0, 'z0': -10, 'x1': 0, 'y1': 0, 'z1': 3, "number_of_lines":30, }
    )
    pile2 = fm.meshPart.create_mesh_part(
        "Line mesh", "Single Line", user_name="beam2", element=beam_ele,
        region=None,
        **{ 'x0': 1, 'y0': 0, 'z0': -10, 'x1': 1, 'y1': 0, 'z1': 3, "number_of_lines":30, }
    )
    pile3 = fm.meshPart.create_mesh_part(
        "Line mesh", "Single Line", user_name="beam3", element=beam_ele,
        region=None,
        **{ 'x0': -1, 'y0': 0, 'z0': -10, 'x1': -1, 'y1': 0, 'z1': 3, "number_of_lines":30, }
    )
    pile4 = fm.meshPart.create_mesh_part(
        "Line mesh", "Single Line", user_name="beam4", element=beam_ele,
        region=None,
        **{ 'x0': 0, 'y0': 1, 'z0': -10, 'x1': 0, 'y1': 1, 'z1': 3, "number_of_lines":30, }
    )
    pile5 = fm.meshPart.create_mesh_part(
        "Line mesh", "Single Line", user_name="beam5", element=beam_ele,
        region=None,
        **{ 'x0': 0, 'y0': -1, 'z0': -10, 'x1': 0, 'y1': -1, 'z1': 3, "number_of_lines":30, }
    )

    # ------------------------------------------------------------------
    # 3. Make assembly & interface
    # ------------------------------------------------------------------
    fm.assembler.create_section(["soil_vol", "cap", "beam1", "beam2", "beam3", "beam4", "beam5"], num_partitions=8, merging_points=False)
    # fm.assembler.create_section(["beam1", "beam2", "beam3", "beam4", "beam5"], num_partitions=8, merging_points=False)
    interface_radius = 0.51  # Radius for the embedded beam-solid interface
    EmbeddedBeamSolidInterface(
        name="EmbedTest", beam_part="beam1", radius=interface_radius,
        n_peri=8, n_long=10, crd_transf_tag=transf.transf_tag,
    )
    EmbeddedBeamSolidInterface(
        name="EmbedTest2", beam_part="beam2", radius=interface_radius,
        n_peri=8, n_long=10, crd_transf_tag=transf.transf_tag,
    )
    EmbeddedBeamSolidInterface(
        name="EmbedTest3", beam_part="beam3", radius=interface_radius,
        n_peri=8, n_long=10, crd_transf_tag=transf.transf_tag,
    )
    EmbeddedBeamSolidInterface(
        name="EmbedTest4", beam_part="beam4", radius=interface_radius,
        n_peri=8, n_long=10, crd_transf_tag=transf.transf_tag,
    )
    EmbeddedBeamSolidInterface(
        name="EmbedTest5", beam_part="beam5", radius=interface_radius,
        n_peri=8, n_long=10, crd_transf_tag=transf.transf_tag,
    )
    # open the gui to visualize the mesh
    fm.assembler.Assemble()
    # fm.gui()

    # pl = pv.Plotter()
    # pl.add_mesh(fm.assembler.AssembeledMesh, color='blue', scalars="Core", opacity=1.0, show_edges=True)
    # pl.show()
    # exit(0)


    # Assemble again to allow interface to move solids if needed
    # exit(0)  # Exit here to avoid exporting TCL if running interactively

 # Exit here to avoid exporting TCL if running interactively
    # import os 
    # # change the directory to the current directory
    # os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # # Export TCL (interface will inject its command)
    # fm.export_to_tcl("embedded_demo.tcl")

    # print("Demo finished → embedded_demo.tcl generated.") 