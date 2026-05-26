from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class TrigTimeSeries(TimeSeries):
    """Sinusoidal load-factor time series for cyclic excitation.

    This time series generates a sinusoidal load factor between ``tStart`` and
    ``tEnd``. Use it for cyclic excitation where amplitude, period, and phase
    shift must be controlled explicitly.

    Tcl form:
        ``timeSeries Trig <tag> <tStart> <tEnd> <period> -factor <factor>
        -shift <shift>``

    Attributes:
        tStart: Start time of the sinusoidal series.
        tEnd: End time of the sinusoidal series.
        period: Period of the sinusoidal cycle.
        factor: Scale factor for the sinusoidal amplitude.
        shift: Phase shift applied to the sinusoidal cycle.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ts = model.time_series.trig(
            tStart=0.0,
            tEnd=10.0,
            period=2.0,
            factor=1.5,
            shift=0.25,
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
        """Create a trigonometric time series.

        Args:
            tStart: Start time of the sinusoidal series.
            tEnd: End time of the sinusoidal series.
            period: Period of the sinusoidal cycle.
            factor: Scale factor for the sinusoidal amplitude.
            shift: Phase shift applied to the sinusoidal cycle.

        Raises:
            ValueError: If ``tStart`` is not less than ``tEnd`` or if
                ``period`` is not greater than ``0``.
        """
        super().__init__("Trig")
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
            str: Tcl ``timeSeries Trig`` command for this object.

        Raises:
            ValueError: If this time series has not been added to a manager.
        """
        return (
            f"timeSeries Trig {self._require_tag()} "
            f"{self.tStart} {self.tEnd} {self.period} "
            f"-factor {self.factor} -shift {self.shift}"
        )
