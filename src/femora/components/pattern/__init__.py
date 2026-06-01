"""---
icon: material/sine-wave
---

Pattern component package for Femora.

This package contains runtime load and excitation pattern definitions
registered through [PatternManager][femora.core.pattern_manager.PatternManager]
and exported to OpenSees Tcl as ``pattern`` commands. Patterns apply static or
dynamic loading through attached loads, uniform excitation time series,
multiple-support ground motions, or DRM datasets.

Normal runtime usage should go through a [Model][femora.core.model.Model]
instance and ``model.pattern.*`` factory methods.
"""

from .h5drm_pattern import H5DRMPattern
from .multiple_support import ImposedMotion, MultipleSupportPattern
from .plain_pattern import PlainPattern
from .uniform_excitation import UniformExcitation

__all__ = [
    "UniformExcitation",
    "H5DRMPattern",
    "PlainPattern",
    "ImposedMotion",
    "MultipleSupportPattern",
]
