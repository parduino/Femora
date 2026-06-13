# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod


class Action(ABC):
    """Abstract base class for TCL-emitting process actions."""

    @abstractmethod
    def to_tcl(self) -> str:
        raise NotImplementedError("Subclasses must implement the 'to_tcl' method.")
