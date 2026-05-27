from __future__ import annotations

from abc import ABC, abstractmethod


class Action(ABC):
    """Abstract base class for TCL-emitting process actions."""

    @abstractmethod
    def to_tcl(self) -> str:
        raise NotImplementedError("Subclasses must implement the 'to_tcl' method.")
