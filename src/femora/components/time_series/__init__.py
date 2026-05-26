"""Time series component package for Femora.

This package contains runtime time-series definitions registered through
[TimeSeriesManager][femora.core.time_series_manager.TimeSeriesManager] and
exported to OpenSees Tcl as ``timeSeries`` commands. Time series define
load-factor histories or recorded motion data used downstream by ground
motions and excitation patterns.

Normal runtime usage should go through a [Model][femora.core.model.Model]
instance and ``model.time_series.*`` factory methods.
"""

from .constant_time_series import ConstantTimeSeries
from .linear_time_series import LinearTimeSeries
from .trig_time_series import TrigTimeSeries
from .ramp_time_series import RampTimeSeries
from .triangular_time_series import TriangularTimeSeries
from .rectangular_time_series import RectangularTimeSeries
from .pulse_time_series import PulseTimeSeries
from .path_time_series import PathTimeSeries

__all__ = [
    "ConstantTimeSeries",
    "LinearTimeSeries",
    "TrigTimeSeries",
    "RampTimeSeries",
    "TriangularTimeSeries",
    "RectangularTimeSeries",
    "PulseTimeSeries",
    "PathTimeSeries",
]
