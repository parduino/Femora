from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Union

import numpy as np

from femora.core.region_base import RegionBase
from femora.core.tagging import CompactRetagPolicy

if TYPE_CHECKING:
    from femora.components.MeshMaker import MeshMaker


class _ElementRegionFactory:
    def __init__(self, manager: "RegionManager"):
        self._manager = manager

    def __call__(self, user_name: str | None = None, damping=None, **kwargs):
        from femora.components.region.regions import ElementRegion

        return self._manager.add(ElementRegion(user_name=user_name, damping=damping, **kwargs))


class _NodeRegionFactory:
    def __init__(self, manager: "RegionManager"):
        self._manager = manager

    def __call__(self, user_name: str | None = None, damping=None, **kwargs):
        from femora.components.region.regions import NodeRegion

        return self._manager.add(NodeRegion(user_name=user_name, damping=damping, **kwargs))


class RegionManager:
    """Local manager for region lifecycle, lookup, and tag assignment."""

    def __init__(self, mesh_maker: MeshMaker):
        from femora.components.MeshMaker import MeshMaker as MeshMakerClass

        if not isinstance(mesh_maker, MeshMakerClass):
            raise TypeError("mesh_maker must be a MeshMaker instance")
        existing_manager = getattr(mesh_maker, "region", None)
        if isinstance(existing_manager, RegionManager):
            raise ValueError("mesh_maker already owns a region manager")

        from femora.components.region.regions import ElementRegion, GlobalRegion, NodeRegion

        self._mesh_maker = mesh_maker
        self._regions: Dict[int, RegionBase] = {}
        self._names: Dict[str, RegionBase] = {}
        self._start_tag = 1
        self._tagging = CompactRetagPolicy[RegionBase]()

        self._global_region = GlobalRegion()
        self.add(self._global_region)

        self.element = _ElementRegionFactory(self)
        self.node = _NodeRegionFactory(self)

    def add(self, region: RegionBase) -> RegionBase:
        from femora.components.region.regions import GlobalRegion

        if not isinstance(region, RegionBase):
            raise TypeError("region must be a RegionBase instance")
        if region._owner is not None and region._owner is not self:
            raise ValueError("Region already belongs to another manager")
        if region.user_name == "Unnamed":
            region.user_name = self._generate_default_name(region)
        if region.user_name in self._names and self._names[region.user_name] is not region:
            raise ValueError(f"Region name '{region.user_name}' already exists in this manager")

        region._owner = self
        if isinstance(region, GlobalRegion):
            region.tag = 0
        else:
            try:
                region.tag = self._tagging.assign_tag(self._regions, region, self._start_tag)
            except ValueError as exc:
                raise ValueError(f"Region tag {region.tag} already exists") from exc

        self._regions[region.tag] = region
        self._names[region.user_name] = region
        return region

    def get(self, identifier: Union[int, str]) -> Optional[RegionBase]:
        if isinstance(identifier, (int, np.integer)):
            return self._regions.get(int(identifier))
        return self._names.get(str(identifier))

    def get_all(self) -> Dict[int, RegionBase]:
        return dict(self._regions)

    def remove(self, identifier: Union[int, str]) -> None:
        region = self.get(identifier)
        if region is not None:
            if region.tag == 0:
                raise ValueError("Cannot remove the global region (tag 0)")
            self._regions.pop(region.tag, None)
            self._names.pop(region.user_name, None)
            region.tag = None
            region._owner = None
            self._reassign_tags()

    def clear(self) -> None:
        from femora.components.region.regions import GlobalRegion

        for region in list(self._regions.values()):
            region.tag = None
            region._owner = None
        self._regions.clear()
        self._names.clear()
        self._global_region = GlobalRegion()
        self.add(self._global_region)

    def set_tag_start(self, start_tag: int) -> None:
        self._start_tag = int(start_tag)
        if self._start_tag < 1:
            raise ValueError("start_tag must be >= 1")
        self._reassign_tags()

    def _reassign_tags(self) -> None:
        non_global = sorted(
            [r for r in self._regions.values() if r.tag != 0],
            key=lambda r: r.tag if r.tag is not None else 0,
        )
        self._regions = {0: self._global_region}
        for i, region in enumerate(non_global):
            region.tag = self._start_tag + i
            self._regions[region.tag] = region
        self._names = {r.user_name: r for r in self._regions.values()}

    def _generate_default_name(self, region: RegionBase) -> str:
        base_name = region.get_type()
        if base_name not in self._names:
            return base_name

        index = 2
        while True:
            candidate = f"{base_name}_{index}"
            if candidate not in self._names:
                return candidate
            index += 1

    @property
    def global_region(self):
        return self._global_region

    def __len__(self) -> int:
        return len(self._regions)

    def __iter__(self):
        return iter(self._regions.values())
