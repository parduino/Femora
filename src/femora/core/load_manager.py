from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

from femora.core.load_base import Load
from femora.core.tagging import CompactRetagPolicy

if TYPE_CHECKING:
    from femora.core.model import Model


class LoadManager:
    """Manager-owned lifecycle and tagging for load objects on one Model."""

    def __init__(self, mesh_maker: Model):
        from femora.core.model import Model as ModelClass

        if not isinstance(mesh_maker, ModelClass):
            raise TypeError("mesh_maker must be a Model instance")
        existing_manager = getattr(mesh_maker, "load", None)
        if isinstance(existing_manager, LoadManager):
            raise ValueError("mesh_maker already owns a load manager")

        self._mesh_maker = mesh_maker
        mesh_maker.load = self
        self._loads: Dict[int, Load] = {}
        self._start_tag = 1
        self._tagging = CompactRetagPolicy[Load]()

    def __len__(self) -> int:
        return len(self._loads)

    def __iter__(self):
        return iter(self._loads.values())

    def add(self, load: Load) -> Load:
        if not isinstance(load, Load):
            raise TypeError("load must be a Load instance")
        if load._owner is None:
            load._owner = self
        elif load._owner is not self:
            raise ValueError("load already belongs to another manager")
        try:
            load.tag = self._tagging.assign_tag(self._loads, load, self._start_tag)
        except ValueError as exc:
            raise ValueError(f"Load tag {load.tag} already exists") from exc
        self._loads[load.tag] = load
        return load

    def node(self, **kwargs) -> Load:
        from femora.components.load.node_load import NodeLoad

        return self.add(NodeLoad(**kwargs))

    def element(self, **kwargs) -> Load:
        from femora.components.load.element_load import ElementLoad

        return self.add(ElementLoad(**kwargs))

    def sp(self, **kwargs) -> Load:
        from femora.components.load.sp_load import SpLoad

        return self.add(SpLoad(**kwargs))

    def get(self, tag: int) -> Optional[Load]:
        return self._loads.get(int(tag))

    def get_all(self) -> Dict[int, Load]:
        return dict(self._loads)

    def remove(self, tag: int) -> None:
        load = self._loads.pop(int(tag), None)
        if load is not None:
            load.tag = None
            load._owner = None
            load.pattern_tag = None
            self._reassign_tags()

    def clear(self) -> None:
        for load in list(self._loads.values()):
            load.tag = None
            load._owner = None
            load.pattern_tag = None
        self._loads.clear()

    def set_tag_start(self, start_tag: int) -> None:
        self._start_tag = self._tagging.validate_start_tag(start_tag)
        self._reassign_tags()

    def _reassign_tags(self) -> None:
        self._tagging.reassign_tags(self._loads, self._start_tag)


__all__ = ["LoadManager"]
