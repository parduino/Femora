# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Iterable, Optional

import numpy as np

if TYPE_CHECKING:
    from femora.core.model import Model


@dataclass
class Group:
    """Named Femora selection owned by one model."""

    name: str
    tag: Optional[int] = field(default=None, init=False)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Group name must not be empty")

    def assign_tag(self, tag: int) -> None:
        self.tag = int(tag)


@dataclass
class ElementGroup(Group):
    """Named selection of assembled mesh cells."""

    cell_indices: np.ndarray = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.cell_indices = np.asarray(self.cell_indices, dtype=np.int64)
        if self.cell_indices.ndim != 1:
            raise ValueError("ElementGroup cell_indices must be a one-dimensional array")
        if self.cell_indices.size == 0:
            raise ValueError("ElementGroup must contain at least one cell")
        if np.any(self.cell_indices < 0):
            raise ValueError("ElementGroup cell_indices must be non-negative")

    def element_tags(self, export_element_tags: Iterable[int]) -> list[int]:
        tags = np.asarray(list(export_element_tags), dtype=np.int64)
        if np.any(self.cell_indices >= tags.size):
            raise ValueError(
                f"ElementGroup '{self.name}' references cells outside the assembled mesh"
            )
        return [int(tag) for tag in tags[self.cell_indices]]

    def to_tcl(self, export_element_tags: Iterable[int]) -> str:
        if self.tag is None:
            raise ValueError(f"ElementGroup '{self.name}' has no OpenSees region tag")
        elements = " ".join(str(tag) for tag in self.element_tags(export_element_tags))
        return f'eval "region {self.tag} -ele {elements}"'


@dataclass
class NodeGroup(Group):
    """Named selection of assembled mesh point indices."""

    point_indices: np.ndarray = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.point_indices = np.asarray(self.point_indices, dtype=np.int64)
        if self.point_indices.ndim != 1:
            raise ValueError("NodeGroup point_indices must be a one-dimensional array")
        if self.point_indices.size == 0:
            raise ValueError("NodeGroup must contain at least one point")
        if np.any(self.point_indices < 0):
            raise ValueError("NodeGroup point_indices must be non-negative")


class ElementGroupNamespace:
    def __init__(self, manager: GroupManager):
        self._manager = manager

    def add(self, group: ElementGroup) -> ElementGroup:
        return self._manager._add_element_group(group)

    def get(self, name: str) -> Optional[ElementGroup]:
        group = self._manager._element_groups.get(name)
        return group if isinstance(group, ElementGroup) else None

    def get_all(self) -> Dict[str, ElementGroup]:
        return dict(self._manager._element_groups)

    def from_cells(self, name: str, cell_indices) -> ElementGroup:
        return self.add(ElementGroup(name=name, cell_indices=cell_indices))

    def from_meshparts(
        self,
        name: str,
        meshparts,
        *,
        line_cells_only: bool = False,
    ) -> ElementGroup:
        mesh = self._manager._mesh_maker.assembled_mesh
        if mesh is None:
            raise ValueError("Element group creation requires an assembled mesh")

        resolved = self._manager._resolve_meshparts(meshparts)
        tags = np.array([int(part.tag) for part in resolved.values()], dtype=np.int64)
        mesh_tags = mesh.cell_data.get("MeshPartTag_celldata")
        if mesh_tags is None:
            raise ValueError("Assembled mesh missing MeshPartTag_celldata cell_data")

        mask = np.isin(mesh_tags.astype(np.int64, copy=False), tags)
        if line_cells_only:
            mask = mask & self._manager._line_cell_mask(mesh)

        cell_indices = np.where(mask)[0]
        if cell_indices.size == 0:
            raise ValueError("No matching cells found for the given meshparts")
        return self.from_cells(name=name, cell_indices=cell_indices)


class NodeGroupNamespace:
    def __init__(self, manager: GroupManager):
        self._manager = manager

    def add(self, group: NodeGroup) -> NodeGroup:
        return self._manager._add_node_group(group)

    def get(self, name: str) -> Optional[NodeGroup]:
        group = self._manager._node_groups.get(name)
        return group if isinstance(group, NodeGroup) else None

    def get_all(self) -> Dict[str, NodeGroup]:
        return dict(self._manager._node_groups)

    def from_points(self, name: str, point_indices) -> NodeGroup:
        return self.add(NodeGroup(name=name, point_indices=point_indices))


class GroupManager:
    """Owns named node and element selections for one model."""

    def __init__(self, mesh_maker: Model):
        from femora.core.model import Model as ModelClass

        if not isinstance(mesh_maker, ModelClass):
            raise TypeError("mesh_maker must be a Model instance")
        existing_manager = getattr(mesh_maker, "group", None)
        if isinstance(existing_manager, GroupManager):
            raise ValueError("mesh_maker already owns a group manager")

        self._mesh_maker = mesh_maker
        mesh_maker.group = self
        self._element_groups: Dict[str, ElementGroup] = {}
        self._node_groups: Dict[str, NodeGroup] = {}
        self.element = ElementGroupNamespace(self)
        self.node = NodeGroupNamespace(self)

    def clear(self) -> None:
        self._element_groups.clear()
        self._node_groups.clear()

    def _next_element_group_tag(self) -> int:
        region_tags = [int(tag) for tag in self._mesh_maker.region.get_all().keys()]
        group_tags = [
            int(group.tag)
            for group in self._element_groups.values()
            if group.tag is not None
        ]
        return max(region_tags + group_tags + [0]) + 1

    def _unique_name(self, groups: Dict[str, Group], name: str) -> str:
        if name not in groups:
            return name
        index = 2
        while f"{name}_{index}" in groups:
            index += 1
        return f"{name}_{index}"

    def _add_element_group(self, group: ElementGroup) -> ElementGroup:
        group.name = self._unique_name(self._element_groups, group.name)
        if group.tag is None:
            group.assign_tag(self._next_element_group_tag())
        self._element_groups[group.name] = group
        return group

    def _add_node_group(self, group: NodeGroup) -> NodeGroup:
        group.name = self._unique_name(self._node_groups, group.name)
        self._node_groups[group.name] = group
        return group

    def _resolve_meshparts(self, meshparts) -> Dict[str, object]:
        if not meshparts:
            raise ValueError("meshparts list must not be empty")
        if isinstance(meshparts, str):
            meshparts = [meshparts]
        elif not isinstance(meshparts, (list, tuple, set)):
            meshparts = [meshparts]

        resolved: Dict[str, object] = {}
        for mp in meshparts:
            if isinstance(mp, str):
                part = self._mesh_maker.meshpart.get(mp)
                if part is None:
                    raise ValueError(f"MeshPart '{mp}' not found")
                resolved[mp] = part
            else:
                from femora.core.meshpart_base import MeshPart

                if isinstance(mp, MeshPart):
                    resolved[mp.user_name] = mp
                else:
                    raise TypeError("meshparts entries must be MeshPart instances or user_name strings")
        return resolved

    def _line_cell_mask(self, mesh) -> np.ndarray:
        mask = np.ones(mesh.n_cells, dtype=bool)
        try:
            import pyvista as pv
        except Exception:
            return mask

        celltypes = getattr(mesh, "celltypes", None)
        if celltypes is None:
            return mask

        line_types = set()
        if hasattr(pv, "CellType"):
            for name in ("LINE", "POLY_LINE"):
                if hasattr(pv.CellType, name):
                    line_types.add(getattr(pv.CellType, name))
        if not line_types:
            return mask
        return np.isin(celltypes, list(line_types))


__all__ = ["Group", "ElementGroup", "NodeGroup", "GroupManager"]
