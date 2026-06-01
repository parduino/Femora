"""---
icon: material/vector-square
---

Region component package for Femora.

This package contains runtime region component classes that define structural
sub-groups of elements and nodes in OpenSees. Regions allow the application
of specific damping models, recorders, or properties to subsets of the model.

Normal runtime usage should go through `Model` manager entry points under the
`model.region` namespace:
- `model.region.element(...)` to define an element-based region
- `model.region.node(...)` to define a node-based region
- `model.region.global_region` is a pre-defined region representing the entire model
"""

from femora.core.region_base import RegionBase
from femora.core.region_manager import RegionManager
from femora.components.region.regions import ElementRegion, GlobalRegion, NodeRegion

__all__ = [
    "RegionBase",
    "RegionManager",
    "GlobalRegion",
    "ElementRegion",
    "NodeRegion",
]
