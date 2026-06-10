# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from typing import Dict, Generic, Optional, Type, TypeVar

from femora.core.analysis_component_base import AnalysisComponent
from femora.core.tagging import CompactRetagPolicy

TComponent = TypeVar("TComponent", bound=AnalysisComponent)


class TaggedComponentManager(Generic[TComponent]):
    """Manager-owned lifecycle and tagging for one analysis component family."""

    def __init__(
        self,
        owner: object,
        component_cls: Type[TComponent],
        registry_attr: str,
    ):
        self._owner = owner
        self._component_cls = component_cls
        self._registry_attr = registry_attr
        self._items: Dict[int, TComponent] = {}
        self._start_tag = 1
        self._tagging = CompactRetagPolicy[TComponent]()

    def add(self, component: TComponent) -> TComponent:
        if not isinstance(component, self._component_cls):
            raise TypeError(f"component must be a {self._component_cls.__name__} instance")
        if component._owner is None:
            component._owner = self
        elif component._owner is not self:
            raise ValueError("component already belongs to another manager")
        try:
            component.tag = self._tagging.assign_tag(self._items, component, self._start_tag)
        except ValueError as exc:
            raise ValueError(f"Component tag {component.tag} already exists") from exc
        self._items[component.tag] = component
        return component

    def create(self, component_type: str, **kwargs) -> TComponent:
        registry: Dict[str, Type[TComponent]] = getattr(self._component_cls, self._registry_attr)
        key = component_type.lower()
        if key not in registry:
            raise ValueError(f"Unknown {self._component_cls.__name__} type: {component_type}")
        return self.add(registry[key](**kwargs))

    def get(self, tag: int) -> Optional[TComponent]:
        return self._items.get(int(tag))

    def get_all(self) -> Dict[int, TComponent]:
        return dict(self._items)

    def remove(self, tag: int) -> None:
        component = self._items.pop(int(tag), None)
        if component is not None:
            component.tag = None
            component._owner = None
            self._reassign_tags()

    def clear(self) -> None:
        for component in list(self._items.values()):
            component.tag = None
            component._owner = None
        self._items.clear()

    def set_tag_start(self, start_tag: int) -> None:
        self._start_tag = self._tagging.validate_start_tag(start_tag)
        self._reassign_tags()

    def get_available_types(self) -> list[str]:
        registry: Dict[str, Type[TComponent]] = getattr(self._component_cls, self._registry_attr)
        return list(registry.keys())

    def _reassign_tags(self) -> None:
        self._tagging.reassign_tags(self._items, self._start_tag)


__all__ = ["TaggedComponentManager"]
