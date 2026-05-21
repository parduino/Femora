from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Dict, List, Optional

from femora.components.event.event_bus import EventBus, FemoraEvent

if TYPE_CHECKING:
    from femora.components.MeshMaker import MeshMaker


class InterfaceBase(ABC):
    """Common logic for all interface objects on one MeshMaker model."""

    def __init__(self, name: str, owners: List[str]) -> None:
        self.name = name
        self.owners = owners
        self._owner: Optional["InterfaceManager"] = None

    def _bind_manager(self, manager: "InterfaceManager") -> None:
        if self._owner is not None and self._owner is not manager:
            raise ValueError("interface already belongs to another manager")
        self._owner = manager
        self._subscribe_events()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def _subscribe_events(self) -> None:
        EventBus.subscribe(FemoraEvent.PRE_ASSEMBLE, self._on_pre_assemble)
        EventBus.subscribe(FemoraEvent.POST_ASSEMBLE, self._on_post_assemble)
        EventBus.subscribe(FemoraEvent.RESOLVE_CORE_CONFLICTS, self._on_resolve_core_conflicts)
        EventBus.subscribe(FemoraEvent.PRE_EXPORT, self._on_pre_export)
        EventBus.subscribe(FemoraEvent.POST_EXPORT, self._on_post_export)
        EventBus.subscribe(FemoraEvent.INTERFACE_ELEMENTS_TCL, self._on_interface_tcl_export)

    def _on_pre_assemble(self, **payload):
        pass

    def _on_post_assemble(self, **payload):
        pass

    def _on_pre_export(self, **payload):
        pass

    def _on_post_export(self, **payload):
        pass

    def _on_resolve_core_conflicts(self, **payload):
        pass

    def _on_interface_tcl_export(self, **payload):
        pass


class InterfaceManager:
    """Model-owned factory and lifecycle for interface objects on one MeshMaker."""

    def __init__(self, mesh_maker: Optional["MeshMaker"] = None) -> None:
        from femora.components.MeshMaker import MeshMaker as MeshMakerClass

        self._interfaces: Dict[str, InterfaceBase] = {}
        if mesh_maker is not None:
            if not isinstance(mesh_maker, MeshMakerClass):
                raise TypeError("mesh_maker must be a MeshMaker instance")
            existing = getattr(mesh_maker, "interface", None)
            if isinstance(existing, InterfaceManager) and existing is not self:
                raise ValueError("mesh_maker already owns an interface manager")
            self._mesh_maker = mesh_maker
            mesh_maker.interface = self

    def add(self, interface: InterfaceBase) -> InterfaceBase:
        if not isinstance(interface, InterfaceBase):
            raise TypeError("interface must be an InterfaceBase instance")
        if interface.name in self._interfaces and self._interfaces[interface.name] is not interface:
            raise ValueError(f"Interface with name '{interface.name}' already exists")
        interface._bind_manager(self)
        self._interfaces[interface.name] = interface
        return interface

    def beam_solid_interface(self, **kwargs) -> InterfaceBase:
        from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface

        kwargs["meshpart"] = self._mesh_maker.meshpart
        return self.add(EmbeddedBeamSolidInterface(**kwargs))

    def node_interface(self, **kwargs) -> InterfaceBase:
        from femora.components.interface.embedded_node_interface import EmbeddedNodeInterface

        kwargs["meshpart"] = self._mesh_maker.meshpart
        return self.add(EmbeddedNodeInterface(**kwargs))

    def create_interface(self, interface_cls, *args, **kwargs) -> InterfaceBase:
        if not issubclass(interface_cls, InterfaceBase):
            raise TypeError("interface_cls must be a subclass of InterfaceBase")
        kwargs["meshpart"] = self._mesh_maker.meshpart
        return self.add(interface_cls(*args, **kwargs))

    def get(self, name: str) -> Optional[InterfaceBase]:
        return self._interfaces.get(name)

    def all(self) -> Dict[str, InterfaceBase]:
        return dict(self._interfaces)

    def clear(self) -> None:
        for interface in self._interfaces.values():
            interface._owner = None
        self._interfaces.clear()
