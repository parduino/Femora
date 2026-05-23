from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Union

from femora.core.recorder_base import Recorder
from femora.core.tagging import CompactRetagPolicy

if TYPE_CHECKING:
    from femora.components.MeshMaker import MeshMaker


class RecorderManager:
    """Manager-owned lifecycle and tagging for recorder objects on one MeshMaker."""

    def __init__(self, mesh_maker: MeshMaker):
        from femora.components.MeshMaker import MeshMaker as MeshMakerClass

        if not isinstance(mesh_maker, MeshMakerClass):
            raise TypeError("mesh_maker must be a MeshMaker instance")
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
        import numpy as np

        from femora.components.recorder.recorders import MPCORecorder

        if node_responses is None:
            node_responses = ["displacement", "velocity", "acceleration"]
        if element_responses is None:
            element_responses = ["force"]

        mm = self._mesh_maker
        mesh = self._mesh_maker.assembled_mesh
        if mesh is None:
            raise ValueError("pile_mpco requires an assembled mesh (call Assemble first).")

        resolved: Dict[str, object] = {}
        if not meshparts:
            raise ValueError("pile_mpco: meshparts list must not be empty.")
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
            raise ValueError("pile_mpco: no matching line-mesh cells for the given meshparts.")

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


__all__ = ["RecorderManager"]
