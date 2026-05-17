from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class ConstantTimeSeries(TimeSeries):
    """OpenSees ``Constant`` time series.

    Represents a time series that applies a constant scale factor to loads,
    displacements, or other quantities throughout an analysis. It is primarily
    used when a time-invariant scaling is desired, such as for static analysis
    where loads are applied as a fraction of their magnitude.

    Tcl form:
        ``timeSeries Constant <tag> -factor <factor>``

    Example:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        # Create a constant time series with a factor of 1.0 (default)
        ts_default = model.timeSeries.constant()
        print(ts_default.tag)

        # Create a constant time series with a specific factor
        ts_scaled = model.timeSeries.constant(factor=0.5)
        print(ts_scaled.tag)

        # This time series can then be assigned to a pattern, for example
        # a uniform excitation pattern for static gravity loads.
        # pattern = model.pattern.uniform_excitation(dof=2, time_series=ts_scaled)
        # print(pattern.tag)
        ```
    """

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
            Tcl command string for the constant time series.
        """
        return f"timeSeries Constant {self._require_tag()} -factor {self.factor}"
