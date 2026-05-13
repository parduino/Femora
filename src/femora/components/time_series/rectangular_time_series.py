from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class RectangularTimeSeries(TimeSeries):
    """OpenSees ``Rectangular`` time series.

    Represents a rectangular wave (or square wave) time series, often used in dynamic
    analysis for excitations that are constant for a period and then change.
    It applies a load factor that transitions between 0 and `factor` at defined
    time intervals based on the start time, end time, and period.

    Tcl form:
        ``timeSeries Rectangular <tag> <tStart> <tEnd> <period>
        -shift <shift> -factor <factor>``

    Examples:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        # Create a rectangular time series that applies a factor of 1.5
        # between t=0.2 and t=1.2, repeating every 0.5 units.
        ts = model.timeSeries.rectangular(
            tStart=0.2, tEnd=1.2, period=0.5, factor=1.5
        )
        print(ts.tag)
        ```
    """

    def __init__(
        self,
        tStart: float = 0.0,
        tEnd: float = 1.0,
        period: float = 1.0,
        factor: float = 1.0,
        shift: float = 0.0,
    ):
        """Create a rectangular wave time series.

        Args:
            tStart: Start time of the wave, determining when the factor first
                becomes active.
            tEnd: End time of the wave, determining when the factor last
                becomes active.
            period: The period of the rectangular wave (duration of one cycle).
            factor: The amplitude of the load factor when the wave is "on".
            shift: A phase shift for the wave, moving its effective start
                relative to `tStart`.

        Raises:
            ValueError: If numeric arguments are invalid, `tStart` is greater
                than or equal to `tEnd`, or `period` is less than or equal to 0.
        """
        super().__init__("Rectangular")
        self.tStart = as_float(tStart, "tStart")
        self.tEnd = as_float(tEnd, "tEnd")
        self.period = as_float(period, "period")
        self.factor = as_float(factor, "factor")
        self.shift = as_float(shift, "shift")
        if self.tStart >= self.tEnd:
            raise ValueError("tStart must be less than tEnd")
        if self.period <= 0:
            raise ValueError("period must be greater than 0")

    def to_tcl(self) -> str:
        """Render this time series as an OpenSees Tcl command.

        Returns:
            Tcl command string for this time series.
        """
        return (
            f"timeSeries Rectangular {self._require_tag()} "
            f"{self.tStart} {self.tEnd} {self.period} "
            f"-shift {self.shift} -factor {self.factor}"
        )
