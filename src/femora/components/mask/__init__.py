"""---
icon: material/filter-outline
---

Mask package for Femora.

This package contains runtime mask component classes that enable post-assembly
spatial and attribute-based queries on nodes and elements.

Normal runtime usage should go through the `Model` mask manager entry point
using the `model.mask` namespace, which provides access to `NodeMask` and 
`ElementMask` builders.
"""

from .mask_base import ElementMask, MeshIndex, NodeMask

__all__ = [
    "ElementMask",
    "MeshIndex",
    "NodeMask",
]
