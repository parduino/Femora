from __future__ import annotations

from typing import List

from femora.core.ground_motion_base import GroundMotion


class InterpolatedGroundMotion(GroundMotion):
    """Interpolated ground motion combining managed ground motions.

    An interpolated ground motion combines previously managed ground motions
    using a list of interpolation factors. Referenced ground motions must
    already have manager-assigned tags because OpenSees references them by tag
    inside the interpolation command.

    Tcl form:
        ``groundMotion <tag> Interpolated <gmTag1> <gmTag2> ... -fact
        <factor1> <factor2> ...``

    Note:
        - Each referenced ground motion must be created through
          ``model.ground_motion.*`` before interpolation.
        - Interpolated ground motions are commonly attached to multiple-support
          patterns through ``add_imposed_motion(...)``.

    Attributes:
        ground_motions: Managed ground motions being combined.
        factors: Interpolation factors aligned with ``ground_motions``.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ts_a = model.time_series.path(dt=0.01, filePath="gm_a.acc")
        ts_b = model.time_series.path(dt=0.01, filePath="gm_b.acc")
        gm_a = model.ground_motion.plain(accel=ts_a)
        gm_b = model.ground_motion.plain(accel=ts_b)
        gm = model.ground_motion.interpolated(
            ground_motions=[gm_a, gm_b],
            factors=[0.6, 0.4],
        )
        pattern = model.pattern.multiple_support()
        pattern.add_imposed_motion(node_tag=10, dof=1, ground_motion=gm)
        print(gm.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        ground_motions: List[GroundMotion],
        factors: List[float],
    ):
        """Create an interpolated ground motion.

        Args:
            ground_motions: Ground motions to combine. Each item must be a
                ``GroundMotion`` instance.
            factors: Interpolation factors. Must have the same length as
                ``ground_motions``.

        Raises:
            ValueError: If the ground-motion list is empty, contains invalid
                objects, the factors list is empty, lengths differ, or factors
                are not numeric.
        """
        super().__init__("Interpolated")

        if not isinstance(ground_motions, (list, tuple)) or not ground_motions:
            raise ValueError("ground_motions must be a non-empty list or tuple")
        if not all(isinstance(gm, GroundMotion) for gm in ground_motions):
            raise ValueError("ground_motions must contain GroundMotion objects")
        if not isinstance(factors, (list, tuple)) or not factors:
            raise ValueError("factors must be a non-empty list or tuple")
        if len(factors) != len(ground_motions):
            raise ValueError("factors must have the same length as ground_motions")

        try:
            factor_values = [float(value) for value in factors]
        except Exception:
            raise ValueError("factors must be numeric")

        self.ground_motions = list(ground_motions)
        self.factors = factor_values

    def to_tcl(self) -> str:
        """Render the ground motion as an OpenSees Tcl command.

        Returns:
            str: Tcl ``groundMotion Interpolated`` command for this object.

        Raises:
            ValueError: If this ground motion or any referenced ground motion
                has not been added to a manager.
        """
        gm_tags = []
        for gm in self.ground_motions:
            if gm.tag is None:
                raise ValueError("Interpolated ground motions must be managed before rendering TCL")
            gm_tags.append(str(gm.tag))
        factors = " ".join(map(str, self.factors))
        return f"groundMotion {self._require_tag()} Interpolated {' '.join(gm_tags)} -fact {factors}"
