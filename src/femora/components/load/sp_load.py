from __future__ import annotations

from typing import Any, List, Optional

from femora.core.load_base import Load


def _coerce_positive_int(value: Any, field: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive integer") from exc
    if number < 1:
        raise ValueError(f"{field} must be a positive integer")
    return number


def _coerce_float(value: Any, field: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc


def _coerce_pids(pids: Any) -> List[int]:
    if not isinstance(pids, (list, tuple)):
        raise ValueError("pids must be a list/tuple of integers")
    try:
        return sorted({int(x) for x in pids})
    except (TypeError, ValueError) as exc:
        raise ValueError("pids must be integers") from exc


class SpLoad(Load):
    """Single-point load for the OpenSees ``sp`` command."""

    def __init__(
        self,
        *,
        dof: int,
        value: float,
        node_tag: Optional[int] = None,
        node_mask: Optional[object] = None,
        pids: Optional[List[int]] = None,
    ) -> None:
        super().__init__()

        if node_mask is not None:
            from femora.components.mask.mask_base import NodeMask

            if not isinstance(node_mask, NodeMask):
                raise ValueError("node_mask must be a NodeMask")

        if node_tag is not None:
            node_tag = _coerce_positive_int(node_tag, "node_tag")

        if node_mask is None and node_tag is None:
            raise ValueError("Either node_tag or node_mask must be specified")

        self.node_tag = node_tag
        self.dof = _coerce_positive_int(dof, "dof")
        self.value = _coerce_float(value, "value")
        self.pids = _coerce_pids(pids) if pids is not None else [0]
        self.node_mask = node_mask

    def to_tcl(self) -> str:
        def wrap_with_pid_for_node(nid: int, s: str) -> str:
            pids = self.pids
            if self.node_mask is not None and hasattr(self.node_mask._mesh, "node_core_map"):
                pids = self.node_mask._mesh.node_core_map[nid] or [0]
            if pids:
                cond = " || ".join(f"($pid == {pid})" for pid in pids)
                return f"if {{{cond}}} {{ {s} }}"
            return s

        if self.node_mask is not None:
            id_list = self.node_mask.to_list()
            tag_list = self.node_mask.to_tags()
            lines: List[str] = []
            for nid, node_tag in zip(id_list, tag_list):
                lines.append(
                    wrap_with_pid_for_node(int(nid), f"sp {int(node_tag)} {self.dof} {self.value}")
                )
            return "\n".join(lines)

        cmd = f"sp {self.node_tag} {self.dof} {self.value}"
        return wrap_with_pid_for_node(int(self.node_tag) if self.node_tag is not None else 0, cmd)


__all__ = ["SpLoad"]
