# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class PulseTimeSeries(TimeSeries):
    """Periodic pulse load-factor time series.

    This time series generates a repeating pulse between ``tStart`` and
    ``tEnd``. It is commonly used for impulsive dynamic loading or simplified
    ground-motion pulses.

    Tcl form:
        ``timeSeries Pulse <tag> <tStart> <tEnd> <period> -width <width>
        -factor <factor> -shift <shift>``

    Attributes:
        tStart: Start time of the pulse series.
        tEnd: End time of the pulse series.
        period: Pulse period.
        width: Pulse width as a fraction of the period.
        factor: Load-factor amplitude.
        shift: Phase shift applied to the pulse train.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ts = model.time_series.pulse(
            tStart=0.1,
            tEnd=10.0,
            period=0.5,
            width=0.2,
            factor=2.0,
        )
        pattern = model.pattern.plain(time_series=ts)
        print(ts.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        tStart: float = 0.0,
        tEnd: float = 1.0,
        period: float = 1.0,
        width: float = 0.5,
        factor: float = 1.0,
        shift: float = 0.0,
    ):
        """Create a periodic pulse time series.

        Args:
            tStart: Start time of the pulse series.
            tEnd: End time of the pulse series.
            period: Pulse period.
            width: Pulse width as a fraction of the period.
            factor: Load-factor amplitude.
            shift: Phase shift applied to the pulse train.

        Raises:
            ValueError: If numeric arguments are invalid, if ``tStart`` is not
                less than ``tEnd``, if ``period`` is not positive, or if
                ``width`` is not between ``0`` and ``1``.
        """
        super().__init__("Pulse")
        self.tStart = as_float(tStart, "tStart")
        self.tEnd = as_float(tEnd, "tEnd")
        self.period = as_float(period, "period")
        self.width = as_float(width, "width")
        self.factor = as_float(factor, "factor")
        self.shift = as_float(shift, "shift")
        if self.tStart >= self.tEnd:
            raise ValueError("tStart must be less than tEnd")
        if self.period <= 0:
            raise ValueError("period must be greater than 0")
        if not 0 < self.width < 1:
            raise ValueError("width must be between 0 and 1")

    def to_tcl(self) -> str:
        """Render this time series as an OpenSees Tcl command.

        Returns:
            str: Tcl ``timeSeries Pulse`` command for this object.

        Raises:
            ValueError: If this time series has not been added to a manager.
        """
        return (
            f"timeSeries Pulse {self._require_tag()} "
            f"{self.tStart} {self.tEnd} {self.period} -width {self.width} "
            f"-factor {self.factor} -shift {self.shift}"
        )
