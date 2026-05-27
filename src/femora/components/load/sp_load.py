from __future__ import annotations

from typing import Any, List, Optional

from femora.core.load_base import Load


def _coerce_positive_int(value: Any, field: str) -> int:
    """Coerce a value to a positive integer.

    Args:
        value: The value to be converted.
        field: The name of the field being validated (for error messages).

    Returns:
        The validated positive integer.

    Raises:
        ValueError: If the value cannot be converted to a positive integer or
            is less than 1.
    """
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive integer") from exc
    if number < 1:
        raise ValueError(f"{field} must be a positive integer")
    return number


def _coerce_float(value: Any, field: str) -> float:
    """Coerce a value to a float.

    Args:
        value: The value to be converted.
        field: The name of the field being validated.

    Returns:
        The validated float value.

    Raises:
        ValueError: If the value cannot be converted to a float.
    """
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc


def _coerce_pids(pids: Any) -> List[int]:
    """Coerce partition IDs to a sorted list of unique integers.

    Args:
        pids: The partition IDs (list or tuple) to be validated.

    Returns:
        A sorted list of unique validated integers.

    Raises:
        ValueError: If the input is not a list or tuple of integer values.
    """
    if not isinstance(pids, (list, tuple)):
        raise ValueError("pids must be a list/tuple of integers")
    try:
        return sorted({int(x) for x in pids})
    except (TypeError, ValueError) as exc:
        raise ValueError("pids must be integers") from exc


class SpLoad(Load):
    """Single-point load component for applying values to a specific degree of freedom.

    SpLoad represents a single-point boundary value applied to a specific DOF
    at a node. It is typically registered under a Plain pattern to prescribe
    displacements or boundary loads.

    Tcl form:
        ``sp <nodeTag> <dof> <value>``

    Note:
        - The degree of freedom (`dof`) is 1-indexed (e.g., 1 for X, 2 for Y).
        - If a `node_mask` is provided, the single-point load is applied to all
          selected nodes.
        - In parallel computing contexts, partition IDs (`pids`) specify which
          processor core(s) should execute the command.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ts = model.time_series.constant(factor=1.0)
        pattern = model.pattern.plain(time_series=ts)

        # Apply a prescribed value of -5.0 to DOF 2 of node 3
        load = pattern.add_load.sp(
            node_tag=3,
            dof=2,
            value=-5.0,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        *,
        dof: int,
        value: float,
        node_tag: Optional[int] = None,
        node_mask: Optional[object] = None,
        pids: Optional[List[int]] = None,
    ) -> None:
        """Create a single-point load component.

        Args:
            dof: 1-indexed degree of freedom (DOF) to apply the value to.
            value: Numerical value of the applied single-point excitation.
            node_tag: Optional explicit tag of the target node.
            node_mask: Optional NodeMask object to apply this load to multiple
                nodes.
            pids: Optional processor partition IDs for parallel execution.

        Raises:
            ValueError: If neither `node_tag` nor `node_mask` is specified,
                if `node_mask` is not a NodeMask, or if input validation fails.
        """
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
        """Render this single-point load as OpenSees Tcl commands.

        Returns:
            The OpenSees sp command string(s) for the node(s).
        """
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
