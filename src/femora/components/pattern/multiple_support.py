# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from typing import List

from femora.core.ground_motion_base import GroundMotion
from femora.core.pattern_base import Pattern


class ImposedMotion:
    """OpenSees imposedMotion entry used inside MultipleSupport excitation patterns.

    This class represents one support boundary constraint that applies a prescribed
    ground motion to a specific node degree-of-freedom within a MultipleSupportPattern.

    Tcl form:
        ``imposedMotion <nodeTag> <dof> <groundMotionTag>``

    Note:
        - Create this entry through
          ``MultipleSupportPattern.add_imposed_motion(...)`` rather than by
          direct construction in normal workflows.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        accel = model.time_series.path(dt=0.01, filePath="support.acc")
        gm = model.ground_motion.plain(accel=accel)
        pattern = model.pattern.multiple_support()
        imposed = pattern.add_imposed_motion(node_tag=1, dof=1, ground_motion=gm)
        print(imposed.to_tcl())
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, node_tag: int, dof: int, ground_motion: GroundMotion):
        """Create an imposed support motion constraint.

        Args:
            node_tag: Tag of the node where the motion is prescribed.
            dof: 1-based degree-of-freedom direction (e.g., 1 for X, 2 for Y, 3 for Z).
            ground_motion: Managed ground motion that defines the boundary excitation history.

        Raises:
            ValueError: If node_tag or dof are not positive integers, or if ground_motion is unmanaged.
        """
        try:
            self.node_tag = int(node_tag)
            self.dof = int(dof)
        except Exception:
            raise ValueError("node_tag and dof must be integers")
        if self.node_tag < 1:
            raise ValueError("node_tag must be a positive integer")
        if self.dof < 1:
            raise ValueError("dof must be a positive integer")
        if not isinstance(ground_motion, GroundMotion):
            raise ValueError("ground_motion must be a GroundMotion object")
        if ground_motion.tag is None:
            raise ValueError("ground_motion must be managed before it is used by imposedMotion")
        self.ground_motion = ground_motion

    def to_tcl(self) -> str:
        """Render this imposed motion as an OpenSees Tcl command.

        Returns:
            str: Tcl command string for this imposedMotion entry.

        Raises:
            ValueError: If the referenced ground motion does not currently have an assigned tag.
        """
        if self.ground_motion.tag is None:
            raise ValueError("ground_motion must have a tag before rendering imposedMotion")
        return f"imposedMotion {self.node_tag} {self.dof} {self.ground_motion.tag}"


class MultipleSupportPattern(Pattern):
    """OpenSees MultipleSupport excitation pattern for multi-support boundary loading.

    This pattern is used to model structures excited by spatially varying ground motions
    at different support nodes. It contains and manages a collection of ImposedMotion
    constraints, automatically registering and deduplicating referenced ground motions.

    Tcl form:
        ``pattern MultipleSupport <patternTag> { <groundMotion...> <imposedMotion...> }``

    Note:
        - Ground motions referenced by the attached imposed motions are automatically registered and deduplicated by tag inside the rendered Tcl command block.
        - Interpolated ground motions will have their dependencies emitted automatically before the dependent ground motion.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        accel = model.time_series.path(dt=0.01, filePath="support.acc")
        gm = model.ground_motion.plain(accel=accel)
        pattern = model.pattern.multiple_support()
        pattern.add_imposed_motion(node_tag=10, dof=1, ground_motion=gm)
        print(pattern.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": [
            "__init__",
            "add_imposed_motion",
            "get_imposed_motions",
            "clear_imposed_motions",
        ],
    }

    def __init__(self):
        """Create an empty multiple-support excitation pattern."""
        super().__init__("MultipleSupport")
        self._imposed_motions: List[ImposedMotion] = []

    def add_imposed_motion(
        self,
        node_tag: int,
        dof: int,
        ground_motion: GroundMotion,
    ) -> ImposedMotion:
        """Create and attach an imposed support motion constraint to this pattern.

        Args:
            node_tag: Tag of the node where the support motion is imposed.
            dof: 1-based degree-of-freedom direction.
            ground_motion: Managed ground motion defining the prescribed excitation history.

        Returns:
            ImposedMotion: The created and attached ImposedMotion instance.

        Raises:
            ValueError: If any input fails validation or if the ground motion belongs to a different Model.
        """
        owner = self._owner
        expected_mesh_maker = getattr(owner, "_mesh_maker", None)
        ground_motion_mesh_maker = getattr(ground_motion._owner, "_mesh_maker", None)
        if ground_motion_mesh_maker is not expected_mesh_maker:
            raise ValueError("ground_motion must belong to the local Model")
        expected_manager = getattr(owner, "_ground_motion_manager", None)
        if expected_manager is not None and ground_motion._owner is not expected_manager:
            raise ValueError("ground_motion must belong to the local GroundMotionManager")
        imposed_motion = ImposedMotion(node_tag, dof, ground_motion)
        self._imposed_motions.append(imposed_motion)
        return imposed_motion

    def get_imposed_motions(self) -> List[ImposedMotion]:
        """Return the imposed motions currently attached to this pattern.

        Returns:
            List[ImposedMotion]: A shallow copy of attached ImposedMotion instances in insertion order.
        """
        return list(self._imposed_motions)

    def clear_imposed_motions(self) -> None:
        """Remove all imposed motions from this pattern."""
        self._imposed_motions.clear()

    def to_tcl(self) -> str:
        """Render this pattern as an OpenSees Tcl block.

        Returns:
            str: Tcl block containing groundMotion and imposedMotion lines.

        Raises:
            ValueError: If the pattern is unmanaged or any referenced ground motion is unmanaged.
        """
        lines = [f"pattern MultipleSupport {self._require_tag()} {{"]
        for ground_motion in self._referenced_ground_motions():
            lines.append(f"\t{ground_motion.to_tcl()}")
        for imposed_motion in self._imposed_motions:
            lines.append(f"\t{imposed_motion.to_tcl()}")
        lines.append("}")
        return "\n".join(lines)

    def _referenced_ground_motions(self) -> List[GroundMotion]:
        """Return referenced ground motions in a dependency-safe rendering order.

        Returns:
            List[GroundMotion]: Ordered ground motions needed by all imposed motions in this
                pattern, ensuring ground motion dependencies are listed before their dependents.

        Raises:
            ValueError: If any referenced ground motion is unmanaged.
        """
        ordered: List[GroundMotion] = []
        seen: set[int] = set()

        def visit(ground_motion: GroundMotion) -> None:
            if ground_motion.tag is None:
                raise ValueError("Referenced ground motions must be managed before rendering TCL")
            for dependency in getattr(ground_motion, "ground_motions", []):
                visit(dependency)
            if ground_motion.tag not in seen:
                seen.add(ground_motion.tag)
                ordered.append(ground_motion)

        for imposed_motion in self._imposed_motions:
            visit(imposed_motion.ground_motion)
        return ordered
