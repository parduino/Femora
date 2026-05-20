from __future__ import annotations

import weakref
from abc import ABC, abstractmethod
from typing import Any, Optional

from femora.core.damping_base import Damping

class RegionBase(ABC):
    """
    Abstract base class for defining regions in a structural model.

    Region objects do not self-register and do not assign their own tags.
    A RegionManager owns lifecycle operations, tag assignment, removal,
    and retagging for a local model context.
    """

    def __init__(self, user_name: str = None, damping: Damping = None):
        self.tag: Optional[int] = None
        self._owner: Optional[Any] = None
        self.user_name = user_name or "Unnamed"
        self._damping = weakref.ref(damping) if damping else None
        self.active = True

    @property
    def tag(self):
        return self._tag if hasattr(self, "_tag") else None

    @tag.setter
    def tag(self, value: Optional[int]):
        self._tag = value

    @property
    def name(self):
        return self.user_name

    @property
    def damping(self):
        return self._damping() if self._damping else None

    @damping.setter
    def damping(self, value: Optional[Damping]):
        if value is not None and not isinstance(value, Damping):
            raise TypeError("damping must be an instance of Damping")
        self._damping = weakref.ref(value) if value else None

    @damping.deleter
    def damping(self):
        self._damping = None

    def set_damping(self, damping_instance: Damping):
        self.damping = damping_instance

    def __str__(self) -> str:
        type_name = self.get_type()
        res = "Region class"
        res += f"\n\tTag: {self.tag}"
        res += f"\n\tName: {self.name}"
        res += f"\n\tType: {type_name}"
        res += f"\n\tActive: {self.active}"
        res += (
            f"\n\tDamping: " + ("\n\t" + str(self.damping)).replace("\n", "\n\t")
            if self.damping
            else "\n\tDamping: None"
        )
        return res

    @abstractmethod
    def to_tcl(self) -> str:
        pass

    @staticmethod
    @abstractmethod
    def get_type() -> str:
        pass
