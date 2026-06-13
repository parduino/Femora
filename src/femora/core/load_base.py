# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class Load(ABC):
    """Base class for OpenSees load commands emitted inside a ``pattern Plain`` block.

    Load instances do not self-register. A :class:`LoadManager` owns tag assignment
    and lifecycle for a single model context.
    """

    def __init__(self) -> None:
        self.tag: Optional[int] = None
        self._owner: Optional[object] = None
        self.pattern_tag: Optional[int] = None

    @abstractmethod
    def to_tcl(self) -> str:
        raise NotImplementedError


__all__ = ["Load"]
