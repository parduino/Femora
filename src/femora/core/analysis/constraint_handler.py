# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from typing import Dict, Type

from femora.core.analysis_component_base import AnalysisComponent


class ConstraintHandler(AnalysisComponent):
    """Base class for OpenSees constraint handlers."""

    _handlers: Dict[str, Type["ConstraintHandler"]] = {}

    def __init__(self, handler_type: str) -> None:
        super().__init__()
        self.handler_type = handler_type

    @staticmethod
    def register_handler(name: str, handler_class: Type["ConstraintHandler"]) -> None:
        ConstraintHandler._handlers[name.lower()] = handler_class


__all__ = ["ConstraintHandler"]
