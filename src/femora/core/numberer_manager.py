from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from femora.components.analysis.numberers import Numberer

if TYPE_CHECKING:
    from femora.core.analysis_manager import AnalysisManager


class NumbererManager:
    """Model-scoped cache of numberer instances (not tag-managed)."""

    def __init__(self, analysis_manager: AnalysisManager) -> None:
        self._analysis_manager = analysis_manager
        self._instances: Dict[str, Numberer] = {}

    def _cached(self, key: str) -> Numberer:
        key = key.lower()
        if key not in self._instances:
            if key not in Numberer._numberers:
                raise ValueError(f"Unknown numberer type: {key}")
            self._instances[key] = Numberer._numberers[key]()
        return self._instances[key]

    def plain(self) -> Numberer:
        return self._cached("plain")

    def rcm(self) -> Numberer:
        return self._cached("rcm")

    def amd(self) -> Numberer:
        return self._cached("amd")

    def parallelrcm(self) -> Numberer:
        return self._cached("parallelrcm")

    def clear(self) -> None:
        self._instances.clear()


__all__ = ["NumbererManager"]
