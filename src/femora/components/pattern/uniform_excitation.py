# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from femora.core.pattern_base import Pattern
from femora.core.time_series_base import TimeSeries


class UniformExcitation(Pattern):
    """Uniform excitation pattern for identical support motion in one DOF direction.

    This pattern applies one managed acceleration time series as boundary
    excitation to a selected global degree-of-freedom direction at all support
    nodes. It references a time series directly rather than a ground motion
    object.

    Tcl form:
        ``pattern UniformExcitation <tag> <dof> -accel <tsTag> [-vel0 <vel0>] [-fact <factor>]``

    Note:
        - Use ``model.time_series.path(...)`` or another managed acceleration
          history before creating this pattern.
        - OpenSees reports nodal responses relative to the support motion, so
          absolute motion interpretation requires post-processing care.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        accel = model.time_series.path(dt=0.01, filePath="ground_motion.acc")
        pattern = model.pattern.uniform_excitation(
            dof=1,
            time_series=accel,
            vel0=0.0,
            factor=1.0,
        )
        print(pattern.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        dof: int,
        time_series: TimeSeries,
        vel0: float = 0.0,
        factor: float = 1.0,
    ):
        """Create a uniform excitation pattern with validated inputs.

        Args:
            dof: 1-based excitation direction (e.g., 1 for X, 2 for Y, 3 for Z).
            time_series: Managed acceleration ``TimeSeries`` object that defines the excitation history.
            vel0: Initial velocity, typically 0.0 unless starting from a known non-zero velocity state.
            factor: Scale factor applied to the acceleration time series.

        Raises:
            ValueError: If dof is not a positive integer, or if time_series is not a managed TimeSeries instance.
        """
        super().__init__("UniformExcitation")
        try:
            self.dof = int(dof)
        except Exception:
            raise ValueError("dof must be an integer")
        if self.dof < 1:
            raise ValueError("dof must be a positive integer")
        if not isinstance(time_series, TimeSeries):
            raise ValueError("time_series must be a TimeSeries object")
        if time_series.tag is None:
            raise ValueError("time_series must be managed before it is used by a pattern")
        self.time_series = time_series
        self.vel0 = float(vel0)
        self.factor = float(factor)

    def to_tcl(self) -> str:
        """Render this pattern as an OpenSees Tcl command.

        Returns:
            str: Tcl command string for the UniformExcitation pattern.

        Raises:
            ValueError: If the pattern has not been assigned a manager tag.
        """
        cmd = f"pattern UniformExcitation {self._require_tag()} {self.dof} -accel {self.time_series.tag}"
        if self.vel0 != 0.0:
            cmd += f" -vel0 {self.vel0}"
        if self.factor != 1.0:
            cmd += f" -fact {self.factor}"
        return cmd
