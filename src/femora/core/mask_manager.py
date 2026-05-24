from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

import numpy as np

from femora.components.mask.mask_base import ElementMask, MeshIndex, NodeMask
from femora.core.event_bus import FemoraEvent

if TYPE_CHECKING:
    from femora.components.MeshMaker import MeshMaker


class MaskManager:
    """MeshMaker-owned post-assembly query service over the assembled mesh."""

    def __init__(self, mesh_maker: "MeshMaker"):
        from femora.components.MeshMaker import MeshMaker as MeshMakerClass

        if not isinstance(mesh_maker, MeshMakerClass):
            raise TypeError("mesh_maker must be a MeshMaker instance")
        self._mesh_maker = mesh_maker
        self._mesh_index: MeshIndex | None = None
        self._events_subscribed = False

    def register_events(self) -> None:
        if self._events_subscribed:
            return
        self._mesh_maker.events.subscribe(
            FemoraEvent.POST_ASSEMBLE, self._handle_post_assemble
        )
        self._events_subscribed = True

    def unregister_events(self) -> None:
        if not self._events_subscribed:
            return
        self._mesh_maker.events.unsubscribe(
            FemoraEvent.POST_ASSEMBLE, self._handle_post_assemble
        )
        self._events_subscribed = False

    def clear(self) -> None:
        """Drop the cached assembled-mesh index snapshot."""
        self._mesh_index = None

    def _handle_post_assemble(self, **kwargs) -> None:
        grid = kwargs.get("assembled_mesh", self._mesh_maker.assembled_mesh)
        if grid is not None:
            self._mesh_index = self._build_index_from_grid(grid.copy())
        else:
            self._mesh_index = None

    def _require_index(self) -> MeshIndex:
        # POST_ASSEMBLE normally builds the cache; this path covers direct access
        # after assembly when the index has not been populated yet.
        if self._mesh_index is None:
            grid = self._mesh_maker.assembled_mesh
            if grid is None:
                raise RuntimeError(
                    "Mask requires an assembled mesh; call assembler.assemble() first"
                )
            self._mesh_index = self._build_index_from_grid(grid.copy())
        return self._mesh_index

    @property
    def nodes(self) -> NodeMask:
        mesh = self._require_index()
        return NodeMask(mesh, mesh.node_ids)

    @property
    def elements(self) -> ElementMask:
        mesh = self._require_index()
        return ElementMask(mesh, mesh.element_ids)

    @staticmethod
    def _build_index_from_grid(grid) -> MeshIndex:
        node_coords = np.asarray(grid.points)
        node_ids = np.arange(node_coords.shape[0], dtype=int)
        node_ndf = np.asarray(
            grid.point_data.get("ndf", np.zeros((node_coords.shape[0],), dtype=int))
        )

        ncells = int(grid.n_cells)
        elem_tags = grid.cell_data.get("ElementTag")
        element_ids = (
            np.asarray(elem_tags, dtype=int) if elem_tags is not None else np.arange(ncells, dtype=int)
        )

        offsets = np.asarray(grid.offset)
        connectivity = np.asarray(grid.cell_connectivity)
        conn_list: List[np.ndarray] = []
        for i, start in enumerate(offsets):
            end = int(offsets[i + 1]) if i + 1 < len(offsets) else int(connectivity.size)
            conn_list.append(connectivity[start:end].astype(int, copy=False))

        element_centroids = np.asarray(grid.cell_centers().points)
        element_types = np.asarray(getattr(grid, "celltypes", np.zeros((ncells,), dtype=int)))
        material_tags = np.asarray(grid.cell_data.get("MaterialTag", np.zeros(ncells, dtype=int)))
        section_tags = np.asarray(grid.cell_data.get("SectionTag", np.zeros(ncells, dtype=int)))
        region_tags = np.asarray(grid.cell_data.get("Region", np.zeros(ncells, dtype=int)))
        core_ids = np.asarray(grid.cell_data.get("Core", np.zeros(ncells, dtype=int)))

        node_core_map: List[List[int]] = [list() for _ in range(node_ids.size)]
        elem_id_to_index: Dict[int, int] = {}
        for idx, eid in enumerate(element_ids.tolist()):
            elem_id_to_index[int(eid)] = idx
            pid = int(core_ids[idx])
            for nidx in conn_list[idx].tolist():
                if pid not in node_core_map[int(nidx)]:
                    node_core_map[int(nidx)].append(pid)

        return MeshIndex(
            node_ids=node_ids,
            node_coords=node_coords,
            element_ids=element_ids,
            element_connectivity=conn_list,
            element_centroids=element_centroids,
            element_types=element_types,
            material_tags=material_tags,
            section_tags=section_tags,
            region_tags=region_tags,
            core_ids=core_ids,
            node_ndf=node_ndf,
            node_core_map=node_core_map,
            element_id_to_index=elem_id_to_index,
        )
