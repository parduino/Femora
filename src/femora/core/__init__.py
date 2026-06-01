"""---
icon: material/cog-outline
---

Femora core package.

The core package contains model-owned managers, shared runtime abstractions,
and lower-level infrastructure that support the higher-level component layer.
"""

from .element_base import Element
from .element_manager import ElementManager
from .ground_motion_base import GroundMotion
from .ground_motion_manager import GroundMotionManager
from .tagging import CompactRetagPolicy, TaggingPolicy, TaggedObject
from femora.components.ground_motion import PlainGroundMotion, InterpolatedGroundMotion
