from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class ConstantTimeSeries(TimeSeries):
    """Constant load-factor time series for time-invariant scaling.

    This time series applies a fixed scale factor throughout an analysis. It is
    commonly used for static load patterns or as a simple multiplier in plain
    load patterns.

    Tcl form:
        ``timeSeries Constant <tag> -factor <factor>``

    Attributes:
        factor: Constant scale factor applied for the whole analysis.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ts = model.time_series.constant(factor=0.5)
        pattern = model.pattern.plain(time_series=ts)
        print(ts.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, factor: float = 1.0):
        """Create a constant time series.

        Args:
            factor: Constant scale factor applied for the whole analysis.

        Raises:
            ValueError: If ``factor`` cannot be converted to ``float``.
        """
        super().__init__("Constant")
        self.factor = as_float(factor, "factor")

    def to_tcl(self) -> str:
        """Render this time series as an OpenSees Tcl command.

        Returns:
            str: Tcl ``timeSeries Constant`` command for this object.

        Raises:
            ValueError: If this time series has not been added to a manager.
        """
        return f"timeSeries Constant {self._require_tag()} -factor {self.factor}"
