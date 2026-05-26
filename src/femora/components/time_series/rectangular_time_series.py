from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class RectangularTimeSeries(TimeSeries):
    """Rectangular-wave load-factor time series.

    This time series applies a load factor that switches between zero and
    ``factor`` over repeating intervals defined by ``tStart``, ``tEnd``, and
    ``period``.

    Tcl form:
        ``timeSeries Rectangular <tag> <tStart> <tEnd> <period>
        -shift <shift> -factor <factor>``

    Attributes:
        tStart: Start time when the wave first becomes active.
        tEnd: End time when the wave last remains active.
        period: Duration of one rectangular-wave cycle.
        factor: Load-factor amplitude when the wave is active.
        shift: Phase shift applied to the wave.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ts = model.time_series.rectangular(
            tStart=0.2,
            tEnd=1.2,
            period=0.5,
            factor=1.5,
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
        """Create a rectangular wave time series.

        Args:
            tStart: Start time when the wave first becomes active.
            tEnd: End time when the wave last remains active.
            period: Duration of one rectangular-wave cycle.
            factor: Load-factor amplitude when the wave is active.
            shift: Phase shift applied to the wave.

        Raises:
            ValueError: If numeric arguments are invalid, if ``tStart`` is not
                less than ``tEnd``, or if ``period`` is not positive.
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
            str: Tcl ``timeSeries Rectangular`` command for this object.

        Raises:
            ValueError: If this time series has not been added to a manager.
        """
        return (
            f"timeSeries Rectangular {self._require_tag()} "
            f"{self.tStart} {self.tEnd} {self.period} "
            f"-shift {self.shift} -factor {self.factor}"
        )
