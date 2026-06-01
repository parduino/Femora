"""---
icon: material/waveform
---

Ground motion component package for Femora.

This package contains runtime ground-motion definitions registered through
[GroundMotionManager][femora.core.ground_motion_manager.GroundMotionManager]
and exported to OpenSees Tcl as ``groundMotion`` commands. Ground motions
combine managed time series and are referenced by excitation patterns such as
multiple-support patterns.

Normal runtime usage should go through a [Model][femora.core.model.Model]
instance and ``model.ground_motion.plain(...)`` or
``model.ground_motion.interpolated(...)``.
"""

from .plain_ground_motion import PlainGroundMotion
from .interpolated_ground_motion import InterpolatedGroundMotion

__all__ = [
    "PlainGroundMotion",
    "InterpolatedGroundMotion",
]
