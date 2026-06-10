# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from typing import List, Optional, Union

from femora.core.ground_motion_base import GroundMotion
from femora.core.time_series_base import TimeSeries


class PlainGroundMotion(GroundMotion):
    """Plain ground motion built from managed time series histories.

    A plain ground motion references one or more managed
    [TimeSeries][femora.core.time_series_base.TimeSeries] objects for
    acceleration, velocity, and displacement. OpenSees uses the supplied
    histories to prescribe support motion through ``imposedMotion`` entries in
    multiple-support patterns.

    Tcl form:
        ``groundMotion <tag> Plain <-accel tsTag> <-vel tsTag> <-disp tsTag>
        <-int integratorType ...> <-fact cFactor>``

    Note:
        - At least one of ``accel``, ``vel``, or ``disp`` must be provided.
        - Time series must be created through ``model.time_series.*`` before
          being passed to ``model.ground_motion.plain(...)``.

    Attributes:
        accel: Optional acceleration time series.
        vel: Optional velocity time series.
        disp: Optional displacement time series.
        integrator: Optional OpenSees integration method for derived histories.
        integrator_args: Optional arguments appended after ``integrator``.
        factor: Constant scale factor for the ground motion.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        accel = model.time_series.path(dt=0.01, filePath="support.acc")
        disp = model.time_series.path(dt=0.01, filePath="support.disp")
        gm = model.ground_motion.plain(accel=accel, disp=disp)
        pattern = model.pattern.multiple_support()
        pattern.add_imposed_motion(node_tag=1, dof=1, ground_motion=gm)
        print(gm.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        accel: Optional[TimeSeries] = None,
        vel: Optional[TimeSeries] = None,
        disp: Optional[TimeSeries] = None,
        integrator: Optional[str] = None,
        integrator_args: Optional[List[Union[int, float, str]]] = None,
        factor: float = 1.0,
    ):
        """Create a plain ground motion.

        Args:
            accel: Acceleration time series. Optional if ``vel`` or ``disp`` is
                provided.
            vel: Velocity time series. Optional if ``accel`` or ``disp`` is
                provided.
            disp: Displacement time series. Optional if ``accel`` or ``vel`` is
                provided.
            integrator: Optional OpenSees integration method, such as
                ``"Trapezoidal"`` or ``"Simpson"``.
            integrator_args: Optional arguments appended after ``integrator`` in
                the ``-int`` option.
            factor: Constant scale factor for the ground motion.

        Raises:
            ValueError: If no time series is provided, a supplied time series is
                not a ``TimeSeries`` object, ``integrator_args`` is not a
                sequence, or ``factor`` is not numeric.
        """
        super().__init__("Plain")

        if accel is None and vel is None and disp is None:
            raise ValueError("At least one of accel, vel, or disp must be provided")
        for name, series in (("accel", accel), ("vel", vel), ("disp", disp)):
            if series is not None and not isinstance(series, TimeSeries):
                raise ValueError(f"{name} must be a TimeSeries object")

        if integrator is not None:
            integrator = str(integrator)
            if not integrator:
                raise ValueError("integrator must not be empty")

        if integrator_args is None:
            integrator_args = []
        if not isinstance(integrator_args, (list, tuple)):
            raise ValueError("integrator_args must be a list or tuple")

        try:
            factor = float(factor)
        except Exception:
            raise ValueError("factor must be numeric")

        self.accel = accel
        self.vel = vel
        self.disp = disp
        self.integrator = integrator
        self.integrator_args = list(integrator_args)
        self.factor = factor

    def to_tcl(self) -> str:
        """Render the ground motion as an OpenSees Tcl command.

        Returns:
            str: Tcl ``groundMotion Plain`` command for this object.

        Raises:
            ValueError: If this ground motion has not been added to a manager.
        """
        cmd = f"groundMotion {self._require_tag()} Plain"
        if self.accel is not None:
            cmd += f" -accel {self.accel.tag}"
        if self.vel is not None:
            cmd += f" -vel {self.vel.tag}"
        if self.disp is not None:
            cmd += f" -disp {self.disp.tag}"
        if self.integrator is not None:
            cmd += f" -int {self.integrator}"
            if self.integrator_args:
                cmd += " " + " ".join(map(str, self.integrator_args))
        if self.factor != 1.0:
            cmd += f" -fact {self.factor}"
        return cmd
