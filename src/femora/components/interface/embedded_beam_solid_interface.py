from __future__ import annotations

from typing import List

import numpy as np
import pyvista as pv

from femora.core.interface_base import InterfaceBase
from femora.components.event.mixins import HandlesDecompositionMixin
from femora.core.meshpart_base import MeshPart
from femora.components.mesh.line_meshparts import SingleLineMesh, StructuredLineMesh
from femora.core.event_bus import FemoraEvent
from femora.components.interface.embedded_info import EmbeddedInfo
from femora.core.region_base import RegionBase


class EmbeddedBeamSolidInterface(InterfaceBase, HandlesDecompositionMixin):
    """Embedded beam-solid contact interface.

    EmbeddedBeamSolidInterface models the kinematic and force contact interaction 
    between line elements (e.g. beam-column piles) and 3D solid elements (e.g. soil). 
    It enforces matching partition cores between the embedded beam elements and 
    overlapping solid elements.

    Tcl form:
        None (renders internally via OpenSees interface-specific TCL commands).

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Create an interface for a piles meshpart within the soil domain
        interface = model.interface.beam_solid_interface(
            name="pile_soil_interface",
            beam_part="piles",
            radius=0.25,
            n_peri=8,
            n_long=5,
            penalty_param=1.0e12,
            g_penalty=True,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    @staticmethod
    def _extract_surface_compat(mesh: pv.DataSet) -> pv.PolyData:
        """Return a surface mesh across PyVista versions.

        Newer PyVista versions support the ``algorithm`` keyword, while older
        versions raise ``TypeError`` for it. This helper keeps current behavior
        explicit when supported and falls back cleanly otherwise.
        """
        try:
            return mesh.extract_surface(algorithm="dataset_surface")
        except TypeError:
            return mesh.extract_surface()

    def __init__(
        self,
        name: str,
        beam_part: 'MeshPart | str | int',
        solid_parts: 'List[MeshPart | str | int] | None' = None,
        shape: str = "circle",
        radius: float = 0.5,
        n_peri: int = 8,
        n_long: int = 10,
        penalty_param: float = 1.0e12,
        g_penalty: bool = True,
        region: 'RegionBase | None' = None,
        write_connectivity: bool = False,
        write_interface: bool = False,
        *,
        meshpart,
    ) -> None:
        """Create an EmbeddedBeamSolidInterface.

        Args:
            name: Unique name of the contact interface.
            beam_part: The beam part instance, name, or tag.
            solid_parts: Optional list of solid part instances, names, or tags.
            shape: Shape profile of the beam cross-section. Defaults to "circle".
            radius: Radius of the beam interface geometry. Defaults to 0.5.
            n_peri: Number of points along the perimeter of the circular section. Defaults to 8.
            n_long: Number of points along the longitudinal axis of the beam. Defaults to 10.
            penalty_param: Penalty stiffness parameter for the constraint. Defaults to 1.0e12.
            g_penalty: If True, uses the geometric penalty formulation. Defaults to True.
            region: Optional region bounding the interface. Not implemented yet.
            write_connectivity: If True, outputs boundary connectivity maps to file. Defaults to False.
            write_interface: If True, outputs boundary mesh surfaces to file. Defaults to False.
            meshpart: MeshPart registry manager from the parent model.

        Raises:
            ValueError: If `beam_part` cannot be resolved or if shape is unsupported.
            TypeError: If argument types are invalid (e.g. `beam_part` is not a line mesh).
            NotImplementedError: If unsupported parameter configurations are provided.
        """
        resolved_beam = meshpart.resolve(beam_part)
        if resolved_beam is None:
            raise ValueError(f"Could not retrieve beam_part '{beam_part}' to a MeshPart.")
        # Enforce beam_part is SingleLineMesh
        if not isinstance(resolved_beam, (SingleLineMesh, StructuredLineMesh)):
            raise TypeError("beam_part must be a SingleLineMesh or StructuredLineMesh instance.")
        
        resolved_soild_parts = []
        if solid_parts is not None:
            if not isinstance(solid_parts, list):
                raise TypeError("soild_parts must be a list of MeshPart instances or their user_names.")
            for part in solid_parts:
                resolved_part = meshpart.resolve(part)
                if resolved_part is None:
                    raise ValueError(f"Could not retrieve solid_part '{part}' to a MeshPart.")
                resolved_soild_parts.append(resolved_part)

        super().__init__(name=name, owners=[resolved_beam.user_name])

        # store references
        self.beam_part = resolved_beam
        self.solid_parts = resolved_soild_parts if len(resolved_soild_parts) > 0 else None
        self.radius = radius
        self.n_peri = n_peri
        self.n_long = n_long
        self.penalty_param = penalty_param
        self.g_penalty = g_penalty
        self._instance_embeddedinfo_list: List[EmbeddedInfo] = [] # Instance-level list to store per-instance EmbeddedInfo
        if shape.lower() not in ["circle"]:
            raise ValueError(f"Unsupported shape '{shape}'. Supported shapes: 'circle'.")
        self.shape = shape
        if region is not None and not isinstance(region, RegionBase):
            raise TypeError("region must be an instance of RegionBase or None.")
        elif region is None:
            self.region = region
        else:
            raise NotImplementedError("Region handling is not implemented yet. Please do not use region parameter for now.")
        self.write_connectivity = write_connectivity
        self.write_interface = write_interface

    def _fork_solid_for_single_beam(self, assembled_mesh: pv.UnstructuredGrid, beam_cells_idx: np.ndarray):
        """Fork the solid mesh surrounding a single beam element.

        This ensures the solid elements within the beam's radius are mapped to
        the same computational core as the beam element for parallel partitioning.

        Args:
            assembled_mesh: The main assembled PyVista grid.
            beam_cells_idx: Array of cell indices for the beam element.

        Raises:
            ValueError: If no beams or solids are found during implicit distance calculations.
            RuntimeError: If this interface is not managed by InterfaceManager.
        """
        # t_start_total = time.time()
        assembled_mesh = assembled_mesh.copy()
        beam_core_array = assembled_mesh.cell_data["Core"][beam_cells_idx]
        unique_cores = np.unique(beam_core_array)
        # sort the unique cores from smallest to largest
        unique_cores = np.sort(unique_cores)
        if unique_cores.size > 1:
            # print(f"[EmbeddedBeamSolidInterface:{self.name}] Multiple cores found for beam cells: {unique_cores}.")
            # print("Moving all beam cells to the first core for consistency.")
            # Move all beam cells to same core (pick first) for safety
            target_core = int(unique_cores[0])
            for c in unique_cores[1:]:
                assembled_mesh.cell_data["Core"][beam_cells_idx[beam_core_array == c]] = target_core
        else:
            # print(f"[EmbeddedBeamSolidInterface:{self.name}] Single core found for beam cells: {unique_cores[0]}.")
            # print("all beam cells are in the same core, core:", unique_cores[0])
            target_core = int(unique_cores[0])


        # Beam cell centers
        # t_start_section = time.time()
        beam_points = assembled_mesh.copy().extract_cells(beam_cells_idx).points
        # print(f"--- Time for beam_points extraction: {time.time() - t_start_section:.4f}s")


        # TODO: need to modify the height since the the tail and head 
        # are not necessarily are the first and last points
        # FIXME: this is a hacky way to get the height of the beam

        # t_start_section = time.time()
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
                               resolution=8,
                               capping=True)  

        # clinder.plot(show_edges=True, opacity=1.0, line_width=2)
        clinder = clinder.clean(inplace=False)  # Clean the cylinder mesh
        # print(f"--- Time for cylinder creation: {time.time() - t_start_section:.4f}s")

        # t_start_section = time.time()
        inner_ind = assembled_mesh.compute_implicit_distance(
            surface=clinder, 
            inplace=False
        ).point_data["implicit_distance"] <= 0
        # print(f"--- Time for initial implicit_distance: {time.time() - t_start_section:.4f}s")

        # find the cells that intersects with the beam line
        intersect_ind = assembled_mesh.find_cells_intersecting_line(beam_tail,
                                                                     beam_head, 
                                                                     tolerance=self.radius)
        if len(intersect_ind) > 0:
            intersect_ind_point_ids = []
            for ind in intersect_ind:
                intersect_ind_point_ids.extend(assembled_mesh.get_cell(ind).point_ids)
        
            intersect_ind_point_ids = np.array(intersect_ind_point_ids)
            # make it 1D array and unique
            # intersect_ind_point_ids = intersect_ind_point_ids.flatten()  # Already 1D
            intersect_ind_point_ids = np.unique(intersect_ind_point_ids)


            inner_ind[intersect_ind_point_ids] = True

                

        # t_start_section = time.time()
        inner = assembled_mesh.extract_points(
            ind=inner_ind,
            include_cells=True,
            adjacent_cells=True,
            progress_bar=False
        )
        # print(f"--- Time for inner mesh extraction: {time.time() - t_start_section:.4f}s")



        beam_elements = inner.celltypes == pv.CellType.LINE
        solid_elements = inner.celltypes == pv.CellType.HEXAHEDRON
        beam_ind = inner.cell_data["vtkOriginalCellIds"][beam_elements]
        solid_ind = inner.cell_data["vtkOriginalCellIds"][solid_elements]

        # TODO: Implement solid parts handling which will confine the interface to use only solid parts
        # given in the solid_parts parameter and not all solid elements
        if self.solid_parts is not None:
            raise NotImplementedError(
                "Solid parts handling is not implemented yet. Please do not use solid_parts parameter for now."
            )


        # save the assembeled mesh indexes to the inner mesh
        inner.cell_data["mesh_ind"] = np.zeros(inner.n_cells, dtype=np.int32)
        inner.cell_data["mesh_ind"][solid_elements] = solid_ind
        inner.cell_data["mesh_ind"][beam_elements] = beam_ind


        # Do a for loop and in every iteration pop up the largest solid mesh from the inner mesh
        solid_mesh = inner.extract_cells(solid_elements, progress_bar=False)
        beam_mesh  = inner.extract_cells(beam_elements, progress_bar=False)
        beams_solids = []
        # t_start_loop = time.time()
        while solid_mesh.n_cells > 0:
            solid_mesh_largest = solid_mesh.extract_largest()
            surf = self._extract_surface_compat(solid_mesh_largest)
            beam_mesh.compute_implicit_distance(surf,inplace=True)
            beams = beam_mesh.point_data["implicit_distance"] <= 0
            beams = beam_mesh.extract_points(beams, include_cells=True, adjacent_cells=True, progress_bar=False)

            if beams.n_cells < 1:
                if solid_mesh_largest.n_cells < 1:
                    raise ValueError("No beams and solids found in the solid mesh.")
                else:
                    # # plot for debugging
                    # pl = pv.Plotter()
                    # pl.add_mesh(solid_mesh_largest, color="blue", opacity=0.5, show_edges=True)
                    # pl.add_mesh(beam_mesh, color="red", opacity=1.0, line_width=5)
                    # # beam tail and head as points
                    # pl.add_mesh(pv.PolyData(beam_tail), color="green", point_size=20, render_points_as_spheres=True)
                    # pl.add_mesh(pv.PolyData(beam_head), color="yellow", point_size=20, render_points_as_spheres=True)
                    # pl.show()
                    # check if the beam is even going through the solid mesh
                    ind = solid_mesh_largest.find_cells_intersecting_line(beam_tail, beam_head, tolerance=0)
                    if len(ind) < 1:
                        pass
                    else:
                        raise ValueError(f"[EmbeddedBeamSolidInterface:{self.name}]: No beams found in the solid mesh, but solids are present. This is unexpected. \
                        probably the beam mesh size is too small. \
                        please increase the number of points in the beam mesh.")
            else:
                if solid_mesh_largest.n_cells < 1:
                    raise ValueError("No solids found in the solid mesh, but beams are present. This is unexpected. contact the developers.")
                

            if beams.n_cells > 0 and solid_mesh_largest.n_cells > 0:
                beams = beams.cell_data["mesh_ind"]
                solids = solid_mesh_largest.cell_data["mesh_ind"]

                if len(beams) > 0 and len(solids) > 0:
                    beams_solids.append((beams, solids))

            # now remove the largset solid mesh from the solid_mesh
            solid_mesh = solid_mesh.extract_values(solid_mesh_largest.cell_data["mesh_ind"] , invert=True, scalars="mesh_ind")
        # print(f"--- Time for while loop: {time.time() - t_start_loop:.4f}s")
      
        
        
        # print("num cells:", assembled_mesh.n_cells)
        # print("num points:", assembled_mesh.n_points)


        if len(beams_solids) == 0:
            return
        

        ef = EmbeddedInfo(beams=beam_ind,
                     core_number= target_core,
                     beams_solids=beams_solids)
        if self._owner is None:
            raise RuntimeError(
                f"EmbeddedBeamSolidInterface '{self.name}' must be managed by InterfaceManager "
                "before recording EmbeddedInfo"
            )
        self._owner._embeddedinfo_list.append(ef)
        self._instance_embeddedinfo_list.append(ef)


        assembled_mesh.cell_data["Core"][inner.cell_data["mesh_ind"]] = target_core

        # print(f"--- Total time for _fork_solid_for_single_beam: {time.time() - t_start_total:.4f}s")

    def _on_post_assemble(self, assembled_mesh: pv.UnstructuredGrid, **kwargs):
        """Post-assemble event listener to map core partitions between beams and solids.

        Args:
            assembled_mesh: The assembled PyVista grid.
            **kwargs: Extra event payload.

        Raises:
            ValueError: If no beam elements are found or structured mesh length is missing.
            TypeError: If `beam_part` is of an invalid mesh type.
        """
        # Collect beam cells indices & compute their mean location
        beam_cells_idx = np.where(assembled_mesh.cell_data["MeshPartTag_celldata"] == self.beam_part.tag)[0]
        if beam_cells_idx.size == 0:
            raise ValueError("No beam elements found in assembled mesh for provided MeshPart")
        
        # if beam_part is SingleLineMesh or StructuredLineMesh do different handling
        if isinstance(self.beam_part, SingleLineMesh):
            # print(f"[EmbeddedBeamSolidInterface:{self.name}] SingleLineMesh detected, forking solid mesh around beam.")
            self._fork_solid_for_single_beam(assembled_mesh, beam_cells_idx)
        elif isinstance(self.beam_part, StructuredLineMesh):
            # Type hint for IDE auto-complete
            beam_mesh: pv.UnstructuredGrid = self.beam_part.mesh.copy()
            norm_x = self.beam_part.normal_x
            norm_y = self.beam_part.normal_y
            norm_z = self.beam_part.normal_z
            offset_1 = self.beam_part.offset_1
            offset_2 = self.beam_part.offset_2
            base_point_x = self.beam_part.base_point_x
            base_point_y = self.beam_part.base_point_y
            base_point_z = self.beam_part.base_point_z
            base_vector_1_x = self.beam_part.base_vector_1_x
            base_vector_1_y = self.beam_part.base_vector_1_y
            base_vector_1_z = self.beam_part.base_vector_1_z
            base_vector_2_x = self.beam_part.base_vector_2_x
            base_vector_2_y = self.beam_part.base_vector_2_y
            base_vector_2_z = self.beam_part.base_vector_2_z
            grid_size_1 = self.beam_part.grid_size_1
            grid_size_2 = self.beam_part.grid_size_2
            spacing_1 = self.beam_part.spacing_1
            spacing_2 = self.beam_part.spacing_2
            length = self.beam_part.length

            if length is None:
                raise ValueError("StructuredLineMesh must have length defined.")

            if grid_size_1 is None or grid_size_2 is None:
                raise ValueError("StructuredLineMesh must have grid_size_1 and grid_size_2 defined.")
            
            if spacing_1 is None or spacing_2 is None:
                raise ValueError("StructuredLineMesh must have spacing_1 and spacing_2 defined.")

            if base_vector_1_x is None or base_vector_1_y is None or base_vector_1_z is None:
                raise ValueError(
                    "StructuredLineMesh must have base_vector_1_x, base_vector_1_y, and base_vector_1_z defined."
                )
            
            if base_vector_2_x is None or base_vector_2_y is None or base_vector_2_z is None:
                raise ValueError(
                    "StructuredLineMesh must have base_vector_2_x, base_vector_2_y, and base_vector_2_z defined."
                )

            if base_point_x is None or base_point_y is None or base_point_z is None:
                raise ValueError(
                    "StructuredLineMesh must have base_point_x, base_point_y, and base_point_z defined."
                )
            
            if offset_1 is None or offset_2 is None:
                raise ValueError("StructuredLineMesh must have offset_1 and offset_2 defined.")

            if norm_x is None or norm_y is None or norm_z is None:
                raise ValueError("StructuredLineMesh must have normal_x, normal_y, and normal_z defined.")

            i_size = int(grid_size_1 * spacing_1 + 2*offset_1) * 1.2 # 1.2 to make sure the plane is larger than the mesh
            j_size = int(grid_size_2 * spacing_2 + 2*offset_2) * 1.2 # 1.2 to make sure the plane is larger than the mesh


            project_beam = pv.PolyData(beam_mesh.points).project_points_to_plane(origin=beam_mesh.center_of_mass(),
                                                                                 normal=(norm_x, norm_y, norm_z))
            project_beam.merge_points(tolerance=1e-3, inplace=True)
            normal = np.array([norm_x, norm_y, norm_z])
            normal = normal / np.linalg.norm(normal)  # Normalize the normal vector
            beamindxes = np.where(assembled_mesh.cell_data["MeshPartTag_celldata"] == self.beam_part.tag)[0]
            for projected_point in project_beam.points:
                point_a = projected_point - 1.1 * normal * length / 2 # 1.1 to make sure the line is longer than the mesh
                point_b = projected_point + 1.1 * normal * length / 2 # 1.1 to make sure the line is longer than the mesh
                indxes = assembled_mesh.find_cells_along_line(point_a, point_b, tolerance=1e-3)
                indxes = np.intersect1d(indxes, beamindxes, assume_unique=True)  # Only keep beam indices
                if indxes.shape[0] == 0:
                    raise ValueError(
                        f"No beam elements found in assembled mesh for projected point {projected_point}."
                    )
                else:
                    # add interface
                    self._fork_solid_for_single_beam(assembled_mesh, indxes)
            
        else:
            raise TypeError("beam_part must be a SingleLineMesh or StructuredLineMesh instance.")

    # ------------------------------------------------------------------
    # Event subscription
    # ------------------------------------------------------------------
    def _subscribe_events(self):  # type: ignore[override]
        """Subscribe this interface to model assembly and TCL export events."""
        events = self._model_events()
        events.subscribe(FemoraEvent.PRE_ASSEMBLE, self._on_pre_assemble)
        events.subscribe(FemoraEvent.POST_ASSEMBLE, self._on_post_assemble)
        events.subscribe(FemoraEvent.EMBEDDED_BEAM_SOLID_TCL, self._on_embedded_beam_solid_tcl_export)

    def _unsubscribe_events(self):  # type: ignore[override]
        """Unsubscribe this interface from all model events."""
        events = self._model_events()
        events.unsubscribe(FemoraEvent.PRE_ASSEMBLE, self._on_pre_assemble)
        events.unsubscribe(FemoraEvent.POST_ASSEMBLE, self._on_post_assemble)
        events.unsubscribe(
            FemoraEvent.EMBEDDED_BEAM_SOLID_TCL, self._on_embedded_beam_solid_tcl_export
        )

    def _on_embedded_beam_solid_tcl_export(self, file_handle, **kwargs):
        """Export OpenSees TCL generation commands for this interface.

        Args:
            file_handle: File-like object to write Tcl script commands to.
            **kwargs: Extra event payload.

        Raises:
            RuntimeError: If the interface is not registered in the manager.
        """
        # print(f"[EmbeddedBeamSolidInterface:{self.name}] Exporting TCL commands.")
        if self._owner is None:
            raise RuntimeError(
                f"EmbeddedBeamSolidInterface '{self.name}' must be managed by InterfaceManager "
                "before TCL export"
            )
        mesh_maker = self._owner._mesh_maker
        crd_transf_tag = self.beam_part.element.get_transformation().tag
        file_handle.write("set Femora_embeddedBeamSolidStartTag [getFemoraMax eleTag]\n")
        file_handle.write("set Femora_embeddedBeamSolidStartTag [expr $Femora_embeddedBeamSolidStartTag + 1]\n")
        ele_start_tag = mesh_maker._start_ele_tag
        core_start_tag = mesh_maker._start_core_tag
        for ii, info in enumerate(self._instance_embeddedinfo_list):
            core = info.core_number + core_start_tag
            file_handle.write("if {$pid == %d} {\n" % core)
            # for beams, solids in info.beams_solids:
            for jj, (beams, solids) in enumerate(info.beams_solids):
                # handle if elements tags are not starting from 1
                beams_str = " -beamEle ".join(str(b + ele_start_tag) for b in beams)
                solids_str = " -solidEle ".join(str(s + ele_start_tag) for s in solids)
                connect_file = f"EmbeddedBeamSolidConnect_{self.name}_beam{ii}_part{jj}.dat"
                interface_file = f"EmbeddedBeamSolidInterface_{self.name}_beam{ii}_part{jj}.dat"
                connect_file = mesh_maker.get_results_folder() + "/" + connect_file
                interface_file = mesh_maker.get_results_folder() + "/" + interface_file
                if self.write_connectivity:
                    file_handle.write("\tif {[file exists %s] == 1} {file delete %s}\n" % (connect_file, connect_file))
                if self.write_interface:
                    file_handle.write("\tif {[file exists %s] == 1} {file delete %s}\n" % (interface_file, interface_file))
                file_handle.write(
                    f"\tset maxEleTag [generateInterfacePoints -beamEle {beams_str} -solidEle {solids_str} {'-gPenalty' if self.g_penalty else ''} " +
                    f"-shape {self.shape}  -nP {self.n_peri} -nL {self.n_long} -crdTransf {crd_transf_tag} -radius {self.radius} " +
                    f"-penaltyParam {self.penalty_param} -startTag $Femora_embeddedBeamSolidStartTag" +
                    f"{f' -connectivity {connect_file}' if self.write_connectivity else ''}" +
                    f"{f' -file {interface_file}' if self.write_interface else ''}]\n"
                    f"\tset EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_startTag $Femora_embeddedBeamSolidStartTag\n"
                    f"\tset EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_endTag $maxEleTag\n"
                    # f"\tputs \"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj} startTag: $EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_startTag\"\n"
                    # f"\tputs \"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_endTag: $EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_endTag\"\n"
                    f"\tset Femora_embeddedBeamSolidStartTag [expr $maxEleTag + 1]\n"
                    # f"\tputs $Femora_embeddedBeamSolidStartTag\n"
                )
            file_handle.write("}\n")
            file_handle.write("barrier\n")

    def _get_recorder(self, 
                      res_type: list[str],
                      dt: 'float | None' = None,
                      results_folder: str = "",
                      ) -> str:
        """Helper method to construct the OpenSees recorder command for the interface.

        Args:
            res_type: List of response variables to record. Supported variables include
                "displacement", "localDisplacement", "axialDisp", "radialDisp", 
                "tangentialDisp", "globalForce", "localForce", "axialForce",
                "radialForce", "tangentialForce", "solidForce", "beamForce", "beamLocalForce".
            dt: Optional time step interval for recording.
            results_folder: Destination folder for output files.

        Returns:
            The OpenSees Tcl recorder command string.

        Raises:
            RuntimeError: If the interface is not registered in the manager.
        """
        if self._owner is None:
            raise RuntimeError(
                f"EmbeddedBeamSolidInterface '{self.name}' must be managed by InterfaceManager "
                "before recorder export"
            )
        mesh_maker = self._owner._mesh_maker
        core_start_tag = mesh_maker._start_core_tag

        cmd = ""
        for ii, info in enumerate(self._instance_embeddedinfo_list):
            core = info.core_number + core_start_tag
            cmd += "if {$pid == %d} {\n" % core
            for jj, (beams, solids) in enumerate(info.beams_solids):
                startEle = f"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_startTag"
                endEle = f"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_endTag"
                for res in res_type:
                    fileName = f"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_{res}.out"
                    fileName = results_folder + fileName
                    deltaT = "-dT %f" % dt if dt is not None else ""
                    cmd += f"\trecorder Element -file {fileName} -time {deltaT} -eleRange ${startEle} ${endEle} {res}\n"
            cmd += "}\n"
        return cmd

    def _on_pre_assemble(self, **payload):
        """Pre-assemble event listener to reset collected EmbeddedInfo objects.

        Args:
            **payload: Event payload.

        Raises:
            RuntimeError: If the interface is not registered in the manager.
        """
        if self._owner is None:
            raise RuntimeError(
                f"EmbeddedBeamSolidInterface '{self.name}' must be managed by InterfaceManager "
                "before pre-assemble handling"
            )
        self._owner._embeddedinfo_list.clear()
        self._instance_embeddedinfo_list.clear()


if __name__ == "__main__":
    """Quick demo – builds a cube soil mesh and a central pile, then creates
    the EmbeddedBeamSolidInterface and exports a TCL file named
    `embedded_demo.tcl`.
    """
    from femora.core.model import Model
    model = Model()

    # ------------------------------------------------------------------
    # 1. Create materials and elements
    # ------------------------------------------------------------------
    soil_mat = model.material.nd.elastic_isotropic(user_name="Soil", E=30e6, nu=0.3, rho=2000)
    brick_ele = model.element.brick.std(ndof=3, material=soil_mat)

    # Beam – needs section + transformation
    beam_sec = model.section.beam.elastic(user_name="PileSection", E=2e11, A=0.05, Iz=1e-4, Iy=1e-4)
    transf = model.transformation.transformation3d("Linear", 0, 1, 0)  # Local y-axis as vecXZ
    beam_ele = model.element.beam.disp(ndof=6, section=beam_sec, transformation=transf)

    # ------------------------------------------------------------------
    # 2. Create mesh parts
    # ------------------------------------------------------------------
    dx = 0.5
    Nx = int((10 - (-10)) / dx)
    Ny = Nx
    Nz = int((0 - (-20)) / dx)

    model.meshpart.volume.uniform_rectangular_grid(
        user_name="soil",
        element=brick_ele,
        region=None,
        x_min=-10, x_max=10, y_min=-10, y_max=10, z_min=-20, z_max=0,
        nx=Nx, ny=Ny, nz=Nz
    )

    model.meshpart.volume.uniform_rectangular_grid(
        user_name="cap",
        element=brick_ele,
        region=None,
        x_min=-5, x_max=5, y_min=-5, y_max=5, z_min=1, z_max=2,
        nx=10//0.25, ny=10//0.25, nz=1//0.25
    )

    piles = model.meshpart.line.structured_lines(
        user_name="piles",
        element=beam_ele,
        base_point_x=-4,
        base_point_y=-4,
        base_point_z=-8,
        base_vector_1_x=1,
        base_vector_1_y=0,
        base_vector_1_z=0,
        base_vector_2_x=0,
        base_vector_2_y=1,
        base_vector_2_z=0,
        normal_x=0,
        normal_y=0,
        normal_z=1,
        grid_size_1=8,
        grid_size_2=8,
        spacing_1=1.0,
        spacing_2=1.0,
        number_of_lines=10,
        length=10, 
        offset_1=0,
        offset_2=0,
    )

    # ------------------------------------------------------------------
    # 3. Make assembly & interface
    # ------------------------------------------------------------------
    model.assembler.create_section(["soil"], num_partitions=8, merge_points=False)
    model.assembler.create_section(["cap", "piles"], num_partitions=4, merge_points=False)
    interface_radius = 0.25  # Radius for the embedded beam-solid interface
    model.interface.beam_solid_interface(
        name="EmbedTest",
        beam_part="piles",
        radius=interface_radius,
        n_peri=8,
        n_long=5,
        penalty_param=1.0e12,
        g_penalty=True,
    )
    
    model.assembler.assemble()

    import os 
    # change the directory to the current directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Export TCL (interface will inject its command)
    model.export_to_tcl("embedded_demo.tcl")
    model.assembler.plot(
        show_edges=True, 
        scalars="Core",
        show_grid=True,
    )

    # print("Demo finished → embedded_demo.tcl generated.")
