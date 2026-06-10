# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class AnalysisComponent(ABC):
    """Base class for OpenSees analysis stack components."""

    def __init__(self) -> None:
        self.tag: Optional[int] = None
        self._owner: Optional[object] = None

    @abstractmethod
    def to_tcl(self) -> str:
        raise NotImplementedError


__all__ = ["AnalysisComponent"]
