from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import ArrayLike
from pykdtree.kdtree import KDTree

from femora.constants import FEMORA_MAX_NDF
from femora.core.event_bus import FemoraEvent
from femora.core.meshpart_base import MeshPart

if TYPE_CHECKING:
    from femora.core.model import Model


class MassManager:
    """Model-owned service for assigning nodal mass arrays.

    Mass data lives on mesh parts before assembly and on the assembled mesh
    after assembly. This manager provides convenience helpers that modify those
    arrays without introducing separate mass objects or registries.
    """

    def __init__(self, mesh_maker: "Model"):
        from femora.core.model import Model as ModelClass

        if not isinstance(mesh_maker, ModelClass):
            raise TypeError("mesh_maker must be a Model instance")
        self._mesh_maker = mesh_maker
        self._events_subscribed = False
        self._region_point_cache: dict[int, np.ndarray] = {}

        self.meshpart = _MeshPartMassHelper(self)
        self.region = _RegionMassHelper(self)
        self.global_ = _GlobalMassHelper(self)

    def register_events(self) -> None:
        if self._events_subscribed:
            return
        self._mesh_maker.events.subscribe(
            FemoraEvent.PRE_ASSEMBLE, self._handle_pre_assemble
        )
        self._events_subscribed = True

    def unregister_events(self) -> None:
        if not self._events_subscribed:
            return
        self._mesh_maker.events.unsubscribe(
            FemoraEvent.PRE_ASSEMBLE, self._handle_pre_assemble
        )
        self._events_subscribed = False

    @staticmethod
    def _pad_mass(vec: ArrayLike, ndf: int) -> np.ndarray:
        """Return a vector of length FEMORA_MAX_NDF with zeros padded / truncated."""
        v = np.asarray(vec, dtype=np.float32).flatten()

        if v.size > FEMORA_MAX_NDF:
            v = v[:FEMORA_MAX_NDF]

        res = np.zeros(FEMORA_MAX_NDF, dtype=np.float32)
        res[: v.size] = v
        return res

    @staticmethod
    def _combine(old: np.ndarray, new: np.ndarray, rule: str) -> np.ndarray:
        if rule == "sum":
            return old + new
        if rule == "override":
            return new
        raise ValueError("combine must be 'sum' or 'override'")

    def _handle_pre_assemble(self, *_, **__):
        """Clear transient region caches before a fresh assembly."""
        self._region_point_cache.clear()

    def clear(self) -> None:
        """Clear manager caches and remove Mass arrays from the current model."""
        self._region_point_cache.clear()

        mesh_maker = self._mesh_maker
        if mesh_maker is None:
            return

        for mp in mesh_maker.meshpart.get_all().values():
            if "Mass" in mp.mesh.point_data:
                del mp.mesh.point_data["Mass"]

        asm = mesh_maker.assembled_mesh
        if asm is not None and "Mass" in asm.point_data:
            del asm.point_data["Mass"]

    def get_meshpart_mass_array(self, meshpart_name: str) -> np.ndarray:
        mp = self._mesh_maker.meshpart.get(meshpart_name)
        if mp is None:
            raise KeyError(f"MeshPart '{meshpart_name}' not found")
        _ensure_mass_array(mp)
        return mp.mesh.point_data["Mass"]

    def get_assembled_mass_array(self) -> Optional[np.ndarray]:
        asm = self._mesh_maker.assembled_mesh
        if asm is None:
            return None
        if "Mass" not in asm.point_data:
            asm.point_data["Mass"] = np.zeros(
                (asm.n_points, FEMORA_MAX_NDF), dtype=np.float32
            )
        return asm.point_data["Mass"]


def _ensure_mass_array(meshpart: MeshPart) -> None:
    if "Mass" not in meshpart.mesh.point_data:
        n = meshpart.mesh.n_points
        meshpart.mesh.point_data["Mass"] = np.zeros((n, FEMORA_MAX_NDF), dtype=np.float32)


class _MeshPartMassHelper:
    """Modify meshpart mass arrays before assembly.

    Meshpart ``Mass`` is authoritative pre-assembly. After assembly, edits
    here are not synced automatically; the user must reassemble manually.
    """

    def __init__(self, manager: MassManager):
        self._mgr = manager

    def add_all(
        self,
        meshpart_name: str,
        mass_vec: ArrayLike,
        *,
        combine: str = "sum",
        filter_fn=None,
    ) -> None:
        mp = self._get_mp(meshpart_name)
        arr = mp.mesh.point_data["Mass"]
        if "ndf" not in mp.mesh.point_data:
            ndf_array = np.full(
                shape=(mp.mesh.n_points,),
                fill_value=mp.element._ndof,
                dtype=np.int8,
            )
        else:
            ndf_array = mp.mesh.point_data["ndf"]
        padded = None
        for idx in range(arr.shape[0]):
            if filter_fn is not None and not filter_fn(idx):
                continue
            ndf = int(ndf_array[idx])
            if padded is None:
                padded = self._mgr._pad_mass(mass_vec, ndf)
            arr[idx] = self._mgr._combine(arr[idx], padded, combine)

    def closest_point(
        self,
        meshpart_name: str,
        xyz: Tuple[float, float, float],
        mass_vec: ArrayLike,
        *,
        combine: str = "sum",
    ) -> int:
        mp = self._get_mp(meshpart_name)
        pts = mp.mesh.points
        tree = KDTree(pts)
        _, idx = tree.query(np.asarray(xyz).reshape(1, -1), k=1)
        idx = int(idx[0])
        self.add_nodes(meshpart_name, [idx], [mass_vec], combine=combine)
        return idx

    def add_nodes(
        self,
        meshpart_name: str,
        point_indices: List[int],
        mass_matrix: List[ArrayLike],
        *,
        combine: str = "sum",
    ) -> None:
        if len(point_indices) != len(mass_matrix):
            raise ValueError("point_indices and mass_matrix must be same length")
        mp = self._get_mp(meshpart_name)
        arr = mp.mesh.point_data["Mass"]
        if "ndf" not in mp.mesh.point_data:
            ndf_array = np.full(
                shape=(mp.mesh.n_points,),
                fill_value=mp.element._ndof,
                dtype=np.int8,
            )
        else:
            ndf_array = mp.mesh.point_data["ndf"]
        for idx, vec in zip(point_indices, mass_matrix):
            ndf = int(ndf_array[idx])
            padded = self._mgr._pad_mass(vec, ndf)
            arr[idx] = self._mgr._combine(arr[idx], padded, combine)

    def _get_mp(self, name: str) -> MeshPart:
        mp = self._mgr._mesh_maker.meshpart.get(name)
        if mp is None:
            raise KeyError(f"MeshPart '{name}' not found")
        _ensure_mass_array(mp)
        return mp


class _RegionMassHelper:
    """Modify assembled-mesh mass for nodes belonging to a region."""

    def __init__(self, manager: MassManager):
        self._mgr = manager

    def add_all(
        self,
        region_tag: int,
        mass_vec: ArrayLike,
        *,
        combine: str = "sum",
    ) -> None:
        asm = self._require_assembled()
        point_ids = self._get_region_point_ids(region_tag, asm)
        self._add_to_points(point_ids, mass_vec, asm, combine)

    def closest_point(
        self,
        region_tag: int,
        xyz: Tuple[float, float, float],
        mass_vec: ArrayLike,
        *,
        combine: str = "sum",
    ) -> int:
        asm = self._require_assembled()
        point_ids = self._get_region_point_ids(region_tag, asm)
        pts = asm.points[point_ids]
        tree = KDTree(pts)
        _, local_idx = tree.query(np.asarray(xyz).reshape(1, -1), k=1)
        global_idx = int(point_ids[int(local_idx[0])])
        self._add_to_points([global_idx], mass_vec, asm, combine)
        return global_idx

    def _require_assembled(self):
        asm = self._mgr._mesh_maker.assembled_mesh
        if asm is None:
            raise RuntimeError("Model must be assembled before using region mass helpers")
        if "Mass" not in asm.point_data:
            asm.point_data["Mass"] = np.zeros(
                (asm.n_points, FEMORA_MAX_NDF), dtype=np.float32
            )
        return asm

    def _get_region_point_ids(self, region_tag: int, asm):
        if region_tag in self._mgr._region_point_cache:
            return self._mgr._region_point_cache[region_tag]
        cell_ids = np.where(asm.cell_data["Region"] == region_tag)[0]
        if cell_ids.size == 0:
            raise KeyError(f"Region tag {region_tag} not present in assembled mesh")
        offsets = asm.offset
        connectivity = asm.cell_connectivity
        point_set: set[int] = set()
        for cid in cell_ids:
            start = offsets[cid]
            end = offsets[cid + 1]
            point_set.update(connectivity[start:end])
        ids = np.fromiter(point_set, dtype=int)
        self._mgr._region_point_cache[region_tag] = ids
        return ids

    def _add_to_points(
        self,
        point_ids: np.ndarray | List[int],
        mass_vec: ArrayLike,
        asm,
        combine: str,
    ) -> None:
        arr = asm.point_data["Mass"]
        ndf_arr = asm.point_data["ndf"]
        for idx in point_ids:
            ndf = int(ndf_arr[idx])
            vec = self._mgr._pad_mass(mass_vec, ndf)
            arr[idx] = self._mgr._combine(arr[idx], vec, combine)


class _GlobalMassHelper:
    """Modify assembled-mesh mass globally."""

    def __init__(self, manager: MassManager):
        self._mgr = manager

    def closest_point(
        self,
        xyz: Tuple[float, float, float],
        mass_vec: ArrayLike,
        *,
        combine: str = "sum",
    ) -> int:
        asm = self._require_assembled()
        pts = asm.points
        tree = KDTree(pts)
        _, idx = tree.query(np.asarray(xyz).reshape(1, -1), k=1)
        idx = int(idx[0])
        self._add_to_points([idx], mass_vec, asm, combine)
        return idx

    def add_all(self, mass_vec: ArrayLike, *, combine: str = "sum") -> None:
        asm = self._require_assembled()
        self._add_to_points(np.arange(asm.n_points), mass_vec, asm, combine)

    def _require_assembled(self):
        asm = self._mgr._mesh_maker.assembled_mesh
        if asm is None:
            raise RuntimeError("Model must be assembled before using global mass helpers")
        if "Mass" not in asm.point_data:
            asm.point_data["Mass"] = np.zeros(
                (asm.n_points, FEMORA_MAX_NDF), dtype=np.float32
            )
        return asm

    def _add_to_points(self, ids, mass_vec, asm, combine) -> None:
        arr = asm.point_data["Mass"]
        ndf_arr = asm.point_data["ndf"]
        for idx in ids:
            ndf = int(ndf_arr[idx])
            vec = self._mgr._pad_mass(mass_vec, ndf)
            arr[idx] = self._mgr._combine(arr[idx], vec, combine)
