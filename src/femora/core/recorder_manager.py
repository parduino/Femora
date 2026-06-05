from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Union

from femora.core.recorder_base import Recorder
from femora.core.tagging import CompactRetagPolicy

if TYPE_CHECKING:
    from femora.core.model import Model


class RecorderManager:
    """Manager-owned lifecycle and tagging for recorder objects on one Model."""

    def __init__(self, mesh_maker: Model):
        from femora.core.model import Model as ModelClass

        if not isinstance(mesh_maker, ModelClass):
            raise TypeError("mesh_maker must be a Model instance")
        existing_manager = getattr(mesh_maker, "recorder", None)
        if isinstance(existing_manager, RecorderManager):
            raise ValueError("mesh_maker already owns a recorder manager")

        self._mesh_maker = mesh_maker
        mesh_maker.recorder = self
        self._recorders: Dict[int, Recorder] = {}
        self._start_tag = 1
        self._tagging = CompactRetagPolicy[Recorder]()

    def add(self, recorder: Recorder) -> Recorder:
        if not isinstance(recorder, Recorder):
            raise TypeError("recorder must be a Recorder instance")
        if recorder._owner is None:
            recorder._owner = self
        elif recorder._owner is not self:
            raise ValueError("recorder already belongs to another manager")
        try:
            recorder.tag = self._tagging.assign_tag(self._recorders, recorder, self._start_tag)
        except ValueError as exc:
            raise ValueError(f"Recorder tag {recorder.tag} already exists") from exc
        self._recorders[recorder.tag] = recorder
        return recorder

    def node(self, **kwargs) -> Recorder:
        from femora.components.recorder.recorders import NodeRecorder

        return self.add(NodeRecorder(**kwargs))

    def drift(self, **kwargs) -> Recorder:
        from femora.components.recorder.recorders import DriftRecorder

        return self.add(DriftRecorder(**kwargs))

    def vtkhdf(self, **kwargs) -> Recorder:
        from femora.components.recorder.recorders import VTKHDFRecorder

        return self.add(VTKHDFRecorder(**kwargs))

    def mpco(self, **kwargs) -> Recorder:
        from femora.components.recorder.recorders import MPCORecorder

        return self.add(MPCORecorder(**kwargs))

    def beam_force(self, **kwargs) -> Recorder:
        from femora.components.recorder.recorders import BeamForceRecorder

        return self.add(BeamForceRecorder(**kwargs))

    def embedded_beam_solid_interface(self, **kwargs) -> Recorder:
        from femora.components.recorder.recorders import EmbeddedBeamSolidInterfaceRecorder

        return self.add(EmbeddedBeamSolidInterfaceRecorder(**kwargs))

    def get(self, tag: int) -> Optional[Recorder]:
        return self._recorders.get(int(tag))

    def get_all(self) -> Dict[int, Recorder]:
        return dict(self._recorders)

    def remove(self, tag: int) -> None:
        recorder = self._recorders.pop(int(tag), None)
        if recorder is not None:
            recorder.tag = None
            recorder._owner = None
            self._reassign_tags()

    def clear(self) -> None:
        for recorder in list(self._recorders.values()):
            recorder.tag = None
            recorder._owner = None
        self._recorders.clear()

    def set_tag_start(self, start_tag: int) -> None:
        self._start_tag = self._tagging.validate_start_tag(start_tag)
        self._reassign_tags()

    def _reassign_tags(self) -> None:
        self._tagging.reassign_tags(self._recorders, self._start_tag)

    def pile_mpco(
        self,
        meshparts,
        file_name: str,
        *,
        delta_t: Optional[float] = None,
        num_steps: Optional[int] = None,
        node_responses: Optional[List[str]] = None,
        element_responses: Optional[List[str]] = None,
        node_sensitivities: Optional[List] = None,
        line_cells_only: bool = True,
        region_name: str = "pile_mpco_region",
    ) -> Recorder:
        from femora.components.recorder.recorders import MPCORecorder

        if node_responses is None:
            node_responses = ["displacement", "velocity", "acceleration"]
        if element_responses is None:
            element_responses = ["force"]

        pile_region, cores_arg = self._create_pile_region_for_meshparts(
            meshparts=meshparts,
            line_cells_only=line_cells_only,
            region_name=region_name,
            caller="pile_mpco",
        )

        return self.add(
            MPCORecorder(
                file_name=file_name,
                node_responses=node_responses,
                element_responses=element_responses,
                node_sensitivities=node_sensitivities or [],
                regions=[pile_region],
                delta_t=delta_t,
                num_steps=num_steps,
                cores=cores_arg,
            )
        )

    def pile_vtkhdf(
        self,
        meshparts,
        file_base_name: str,
        *,
        resp_types: Optional[List[str]] = None,
        delta_t: Optional[float] = None,
        r_tol_dt: Optional[float] = None,
        line_cells_only: bool = True,
        region_name: str = "pile_vtkhdf_region",
    ) -> Recorder:
        from femora.components.recorder.recorders import VTKHDFRecorder

        if resp_types is None:
            resp_types = ["disp", "vel", "accel", "force3D", "localForce3D"]

        pile_region, cores_arg = self._create_pile_region_for_meshparts(
            meshparts=meshparts,
            line_cells_only=line_cells_only,
            region_name=region_name,
            caller="pile_vtkhdf",
        )

        return self.add(
            VTKHDFRecorder(
                file_base_name=file_base_name,
                resp_types=resp_types,
                delta_t=delta_t,
                r_tol_dt=r_tol_dt,
                region=pile_region,
                cores=cores_arg,
            )
        )

    def _create_pile_region_for_meshparts(
        self,
        *,
        meshparts,
        line_cells_only: bool,
        region_name: str,
        caller: str,
    ):
        import numpy as np

        mm = self._mesh_maker
        mesh = self._mesh_maker.assembled_mesh
        if mesh is None:
            raise ValueError(f"{caller} requires an assembled mesh (call Assemble first).")

        resolved: Dict[str, object] = {}
        if not meshparts:
            raise ValueError(f"{caller}: meshparts list must not be empty.")
        for mp in meshparts:
            if isinstance(mp, str):
                part = mm.meshpart.get(mp)
                if part is None:
                    raise ValueError(f"MeshPart '{mp}' not found")
                resolved[mp] = part
            else:
                from femora.core.meshpart_base import MeshPart

                if isinstance(mp, MeshPart):
                    resolved[mp.user_name] = mp
                else:
                    raise TypeError("meshparts entries must be MeshPart instances or user_name strings")

        tags = np.array([int(p.tag) for p in resolved.values()], dtype=np.int64)
        mesh_tags = mesh.cell_data.get("MeshPartTag_celldata")
        cores_arr = mesh.cell_data.get("Core")
        region_arr = mesh.cell_data.get("Region")
        if mesh_tags is None or cores_arr is None or region_arr is None:
            raise ValueError(
                "Assembled mesh missing MeshPartTag_celldata, Core, or Region cell_data."
            )

        mask = np.isin(mesh_tags.astype(np.int64, copy=False), tags)
        if line_cells_only:
            try:
                import pyvista as pv
            except Exception:
                pv = None
            if pv is not None:
                celltypes = getattr(mesh, "celltypes", None)
                if celltypes is not None:
                    beam_types = set()
                    if hasattr(pv, "CellType"):
                        for name in ("LINE", "POLY_LINE"):
                            if hasattr(pv.CellType, name):
                                beam_types.add(getattr(pv.CellType, name))
                    if beam_types:
                        beam_mask = np.isin(celltypes, list(beam_types))
                        mask = mask & beam_mask

        idxs = np.where(mask)[0]
        if idxs.size == 0:
            raise ValueError(f"{caller}: no matching line-mesh cells for the given meshparts.")

        pile_region = mm.region.element()
        pile_region._name = region_name

        rtag = int(pile_region.tag)
        region_arr = np.asarray(region_arr)
        region_arr[idxs] = rtag
        mesh.cell_data["Region"] = region_arr

        selected_cores = np.unique(cores_arr[idxs])
        selected_cores = [
            int(c)
            for c in selected_cores
            if isinstance(c, (int, np.integer)) and int(c) >= 0
        ]
        cores_arg: Optional[Union[int, List[int]]] = None
        if selected_cores:
            cores_arg = selected_cores[0] if len(selected_cores) == 1 else selected_cores

        return pile_region, cores_arg


__all__ = ["RecorderManager"]
