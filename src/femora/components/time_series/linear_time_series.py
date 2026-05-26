from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class LinearTimeSeries(TimeSeries):
    """Linear load-factor time series for monotonic ramping.

    This time series scales load factors linearly with pseudo-time, optionally
    multiplied by a user-defined factor. Use it when a monotonic linear ramp is
    needed for static or transient loading definitions.

    Tcl form:
        ``timeSeries Linear <tag> -factor <factor>``

    Attributes:
        factor: Scale factor applied to pseudo-time.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ts = model.time_series.linear(factor=0.75)
        pattern = model.pattern.plain(time_series=ts)
        print(ts.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

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
            str: Tcl ``timeSeries Linear`` command for this object.

        Raises:
            ValueError: If this time series has not been added to a manager.
        """
        return f"timeSeries Linear {self._require_tag()} -factor {self.factor}"
