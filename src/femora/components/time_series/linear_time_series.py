from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class LinearTimeSeries(TimeSeries):
    """OpenSees ``Linear`` time series component.

    This time series scales load factors linearly with pseudo-time, optionally
    multiplied by a user-defined factor. Use it when a monotonic linear ramp is
    needed for static or transient loading definitions.

    Tcl form:
        ``timeSeries Linear <tag> -factor <factor>``

    Attributes:
        tag: Manager-assigned identifier after the object is added to a Femora
            time-series manager.
        factor: Scale factor applied to pseudo-time.

    Example:
        ```python
        import femora as fm

        model = fm.Model()
        ts = model.timeSeries.linear(factor=0.75)
        print(ts.tag)
        print(ts.to_tcl())
        ```
    """

    def __init__(self, factor: float = 1.0):
        """Create a linearly varying time series.

        Args:
            factor: Scale factor applied to pseudo-time.

        Raises:
            ValueError: If ``factor`` cannot be converted to ``float``.
        """
        super().__init__("Linear")
        self.factor = as_float(factor, "factor")

    def to_tcl(self) -> str:
        """Render this time series as an OpenSees Tcl command.

        Returns:
            Tcl command string for the linear time series.
        """
        return f"timeSeries Linear {self._require_tag()} -factor {self.factor}"
