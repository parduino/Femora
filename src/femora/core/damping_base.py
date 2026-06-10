# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from femora.core.tagging import TaggedObject


class Damping(TaggedObject, ABC):
    """Base class for manager-owned damping models."""

    def __init__(self, user_name: Optional[str] = None):
        self.tag: Optional[int] = None
        self._owner: Optional[object] = None
        self.user_name = user_name or "UnnamedDamping"

    @property
    def name(self):
        if self.tag is not None:
            return f"damping{self.tag}"
        return self.user_name

    def remove(self):
        if self._owner is not None and hasattr(self._owner, "remove"):
            self._owner.remove(self.tag)

    def __str__(self) -> str:
        tag_str = str(self.tag) if self.tag is not None else "unmanaged"
        res = f"Damping Class:\t{self.__class__.__name__}"
        res += f"\n\tName: {self.name}"
        res += f"\n\tTag: {tag_str}"
        return res

    @abstractmethod
    def to_tcl(self) -> str:
        pass
