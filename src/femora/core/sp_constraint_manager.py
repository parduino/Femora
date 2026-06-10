# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from typing import Dict, List, Optional

from femora.core.constraint_base import SPConstraint
from femora.core.tagging import CompactRetagPolicy


class SpConstraintManager:
    """Local manager for single-point constraint lifecycle and tag assignment."""

    def __init__(self, owner):
        from femora.core.constraint_manager import ConstraintManager as ConstraintManagerClass

        if not isinstance(owner, ConstraintManagerClass):
            raise TypeError("owner must be a ConstraintManager instance")
        if getattr(owner, "sp", None) is not None:
            raise ValueError("constraint manager already owns SP constraints")

        self._owner = owner
        self._constraints: Dict[int, SPConstraint] = {}
        self._start_tag = 1
        self._tagging = CompactRetagPolicy[SPConstraint]()

    def __len__(self) -> int:
        return len(self._constraints)

    def __iter__(self):
        return iter(self._constraints.values())

    def add(self, constraint: SPConstraint) -> SPConstraint:
        if not isinstance(constraint, SPConstraint):
            raise TypeError("constraint must be a SPConstraint instance")
        if constraint._owner is None:
            constraint._owner = self
        elif constraint._owner is not self:
            raise ValueError("constraint already belongs to another manager")
        try:
            constraint.tag = self._tagging.assign_tag(self._constraints, constraint, self._start_tag)
        except ValueError as exc:
            raise ValueError(f"Constraint tag {constraint.tag} already exists") from exc
        self._constraints[constraint.tag] = constraint
        return constraint

    def fix(self, node_tag: int, dofs: List[int]):
        from femora.components.constraint.sp_constraints import FixConstraint

        return self.add(FixConstraint(node_tag, dofs))

    def fix_x(self, xCoordinate: float, dofs: List[int], tol: float = 1e-10):
        from femora.components.constraint.sp_constraints import FixXConstraint

        return self.add(FixXConstraint(xCoordinate, dofs, tol))

    def fix_y(self, yCoordinate: float, dofs: List[int], tol: float = 1e-10):
        from femora.components.constraint.sp_constraints import FixYConstraint

        return self.add(FixYConstraint(yCoordinate, dofs, tol))

    def fix_z(self, zCoordinate: float, dofs: List[int], tol: float = 1e-10):
        from femora.components.constraint.sp_constraints import FixZConstraint

        return self.add(FixZConstraint(zCoordinate, dofs, tol))

    def fix_macro_x_min(self, dofs: List[int], tol: float = 1e-10):
        from femora.components.constraint.sp_constraints import FixMacroX_min

        return self.add(FixMacroX_min(dofs, tol))

    def fix_macro_x_max(self, dofs: List[int], tol: float = 1e-10):
        from femora.components.constraint.sp_constraints import FixMacroX_max

        return self.add(FixMacroX_max(dofs, tol))

    def fix_macro_y_min(self, dofs: List[int], tol: float = 1e-10):
        from femora.components.constraint.sp_constraints import FixMacroY_min

        return self.add(FixMacroY_min(dofs, tol))

    def fix_macro_y_max(self, dofs: List[int], tol: float = 1e-10):
        from femora.components.constraint.sp_constraints import FixMacroY_max

        return self.add(FixMacroY_max(dofs, tol))

    def fix_macro_z_min(self, dofs: List[int], tol: float = 1e-10):
        from femora.components.constraint.sp_constraints import FixMacroZ_min

        return self.add(FixMacroZ_min(dofs, tol))

    def fix_macro_z_max(self, dofs: List[int], tol: float = 1e-10):
        from femora.components.constraint.sp_constraints import FixMacroZ_max

        return self.add(FixMacroZ_max(dofs, tol))

    def get(self, tag: int) -> Optional[SPConstraint]:
        return self._constraints.get(int(tag))

    def get_all(self) -> Dict[int, SPConstraint]:
        return dict(self._constraints)

    def remove(self, tag: int) -> None:
        constraint = self._constraints.pop(int(tag), None)
        if constraint is not None:
            constraint.tag = None
            constraint._owner = None
            self._reassign_tags()

    def to_tcl(self) -> str:
        from femora.components.constraint.sp_constraints import (
            FixConstraint,
            FixXConstraint,
            FixYConstraint,
            FixZConstraint,
        )

        tcl_commands = []
        fix_constraints = []
        fix_x_constraints = []
        fix_y_constraints = []
        fix_z_constraints = []

        for constraint in self._constraints.values():
            if isinstance(constraint, FixConstraint):
                fix_constraints.append(constraint)
            elif isinstance(constraint, FixXConstraint):
                fix_x_constraints.append(constraint)
            elif isinstance(constraint, FixYConstraint):
                fix_y_constraints.append(constraint)
            elif isinstance(constraint, FixZConstraint):
                fix_z_constraints.append(constraint)

        if fix_constraints:
            tcl_commands.append("# Node-specific constraints")
            for constraint in fix_constraints:
                tcl_commands.append(constraint.to_tcl())

        if fix_x_constraints:
            tcl_commands.append("\n# X-coordinate constraints")
            for constraint in fix_x_constraints:
                tcl_commands.append(constraint.to_tcl())

        if fix_y_constraints:
            tcl_commands.append("\n# Y-coordinate constraints")
            for constraint in fix_y_constraints:
                tcl_commands.append(constraint.to_tcl())

        if fix_z_constraints:
            tcl_commands.append("\n# Z-coordinate constraints")
            for constraint in fix_z_constraints:
                tcl_commands.append(constraint.to_tcl())

        return "\n".join(tcl_commands)

    def clear(self) -> None:
        for constraint in list(self._constraints.values()):
            constraint.tag = None
            constraint._owner = None
        self._constraints.clear()

    def set_tag_start(self, start_tag: int) -> None:
        self._start_tag = self._tagging.validate_start_tag(start_tag)
        self._reassign_tags()

    def _reassign_tags(self) -> None:
        self._tagging.reassign_tags(self._constraints, self._start_tag)


__all__ = ["SpConstraintManager"]
