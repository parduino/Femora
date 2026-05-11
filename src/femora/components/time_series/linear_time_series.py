from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class LinearTimeSeries(TimeSeries):
    """OpenSees Linear time series.

    Represents a time series that varies linearly with time. The load factor is
    calculated as the product of a user-defined factor and the current
    pseudo-time in the domain.

    Tcl form:
        ``timeSeries Linear <tag> -factor <factor>``

    Attributes:
        tag: Manager-assigned identifier after the object is added to a Femora
            manager.
        factor: Scale factor applied to pseudo-time.

    Examples:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        ts = model.timeSeries.linear(factor=1.0)
        print(ts.tag)
        ```
    """

    def __init__(self, factor: float = 1.0):
        """Create a linearly varying time series.

        Args:
            factor: Scale factor applied to pseudo-time.

        Raises:
            ValueError: If the provided factor cannot be converted to a float.
        """
        super().__init__("Linear")
        self.factor = as_float(factor, "factor")

    def to_tcl(self) -> str:
        """Render this time series as an OpenSees Tcl command.

        Returns:
            Tcl command string for this time series.
        """
        return f"timeSeries Linear {self._require_tag()} -factor {self.factor}"