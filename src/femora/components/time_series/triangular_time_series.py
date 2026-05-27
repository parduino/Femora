from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class TriangularTimeSeries(TimeSeries):
    """Triangular-wave load-factor time series.

    This time series generates a triangular wave between ``tStart`` and
    ``tEnd``. It is useful for cyclic or piecewise-linear load-factor histories
    in dynamic analyses.

    Tcl form:
        ``timeSeries Triangular <tag> <tStart> <tEnd> <period>
        -factor <factor> -shift <shift>``

    Attributes:
        tStart: Start time of the triangular wave.
        tEnd: End time of the triangular wave.
        period: Wave period.
        factor: Scale factor for wave amplitude.
        shift: Phase shift applied to the wave.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ts = model.time_series.triangular(
            tStart=0.0,
            tEnd=10.0,
            period=2.0,
            factor=1.5,
            shift=0.5,
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
        factor: float = 1.0,
        shift: float = 0.0,
    ):
        """Create a triangular time series.

        Args:
            tStart: Start time of the triangular wave.
            tEnd: End time of the triangular wave.
            period: Period of the triangular wave.
            factor: Scale factor applied to the wave amplitude.
            shift: Phase shift applied to the wave.

        Raises:
            ValueError: If numeric arguments are invalid, if ``tStart`` is not
                less than ``tEnd``, or if ``period`` is not positive.
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
        """Render this time series as an OpenSees Tcl command.

        Returns:
            str: Tcl ``timeSeries Triangular`` command for this object.

        Raises:
            ValueError: If this time series has not been added to a manager.
        """
        return (
            f"timeSeries Triangular {self._require_tag()} "
            f"{self.tStart} {self.tEnd} {self.period} "
            f"-factor {self.factor} -shift {self.shift}"
        )
