from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class SPConstraint(ABC):
    """Base class for OpenSees single-point constraints."""

    def __init__(self, node_tag: int, dofs: List[int]):
        self.node_tag = node_tag
        self.dofs = dofs
        self.tag: Optional[int] = None
        self._owner: Optional[object] = None

    @abstractmethod
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees."""
        raise NotImplementedError


class MPConstraint(ABC):
    """Base class for OpenSees multi-point constraints."""

    def __init__(self, master_node: int, slave_nodes: List[int]):
        self.master_node = master_node
        self.slave_nodes = slave_nodes
        self.tag: Optional[int] = None
        self._owner: Optional[object] = None

    @abstractmethod
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees."""
        raise NotImplementedError


__all__ = ["SPConstraint", "MPConstraint"]
