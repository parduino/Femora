"""---
icon: material/rotate-orbit
---

Geometry-operations package for Femora.

This package contains spatial transformation helpers and mesh-part transform
proxies used to manipulate geometry-related state around the mesh assembly
workflow.
"""

from .spatial_transform_manager import SpatialTransformManager
from .meshpart_transform_proxy import MeshPartTransform

__all__ = ["SpatialTransformManager", "MeshPartTransform"]


