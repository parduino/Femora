from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class TriangularTimeSeries(TimeSeries):
    """Represents an OpenSees ``Triangular`` time series.

    This time series generates a triangular wave, commonly used to define
    time-dependent loads or ground motion records in OpenSees models.
    It's defined by its start time, end time, period, a factor for amplitude,
    and a phase shift.

    Tcl form:
        ``timeSeries Triangular <tag> <tStart> <tEnd> <period>
        -factor <factor> -shift <shift>``

    Attributes:
        tag: Manager-assigned identifier after the object is added to a Femora
            manager.

    Example:
        ```python
        import femora as fm

        model = fm.Model()
        # Create a triangular time series starting at 0, ending at 10, with period 2
        ts = model.timeSeries.triangular(
            tStart=0.0,
            tEnd=10.0,
            period=2.0,
            factor=1.5,
            shift=0.5
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
        """Initialize a TriangularTimeSeries instance.

        Args:
            tStart: The start time of the triangular wave.
            tEnd: The end time of the triangular wave.
            period: The period of the triangular wave.
            factor: A scaling factor applied to the wave amplitude.
            shift: A phase shift applied to the wave.

        Raises:
            ValueError: If any numeric argument is non-numeric,
                ``tStart`` is greater than or equal to ``tEnd``,
                or ``period`` is less than or equal to 0.
        """
        super().__init__("Triangular")
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
        """Render this time series as an OpenSees Tcl command string.

        Returns:
            A string representing the OpenSees Tcl command for this triangular
            time series.
        """
        return (
            f"timeSeries Triangular {self._require_tag()} "
            f"{self.tStart} {self.tEnd} {self.period} "
            f"-factor {self.factor} -shift {self.shift}"
        )
