from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class PulseTimeSeries(TimeSeries):
    """Represents an OpenSees ``Pulse`` time series.

    This time series generates a periodic pulse function with configurable
    start time, end time, period, width, amplitude factor, and phase shift.
    It is typically used to define dynamic loads or ground motions that
    exhibit a pulse-like behavior over a specified duration.

    Tcl form:
        ``timeSeries Pulse <tag> <tStart> <tEnd> <period> -width <width>
        -factor <factor> -shift <shift>``

    Example:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        # Create a pulse time series for a load with a 0.5s period, 0.2 width
        # starting at 0.1s and ending at 10.0s
        pulse_ts = model.timeSeries.pulse(
            tStart=0.1, tEnd=10.0, period=0.5, width=0.2, factor=2.0
        )
        print(pulse_ts.tag)
        ```
    """

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
            factor: Load factor amplitude.
            shift: Phase shift.

        Raises:
            ValueError: If numeric arguments are invalid, ``tStart >= tEnd``,
                ``period <= 0``, or ``width`` is not between ``0`` and ``1``.
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
            A string representing the OpenSees Tcl command for this pulse time series.
        """
        return (
            f"timeSeries Pulse {self._require_tag()} "
            f"{self.tStart} {self.tEnd} {self.period} -width {self.width} "
            f"-factor {self.factor} -shift {self.shift}"
        )
