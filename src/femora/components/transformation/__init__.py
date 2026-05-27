"""Geometric transformation component package for Femora.

This package contains runtime geometric transformation component classes that
represent OpenSees coordinate transformation commands (``geomTransf``). These
objects define how beam-column elements transform nodal forces and displacements
between local and global coordinate systems.

Normal runtime usage should go through `Model` manager entry points under the
`model.transformation` namespace:
- `model.transformation.transformation2d(...)` for 2D coordinate transformations
- `model.transformation.transformation3d(...)` for 3D coordinate transformations
"""

from femora.components.transformation.transformation import (
    GeometricTransformation,
    GeometricTransformation2D,
    GeometricTransformation3D,
)

__all__ = [
    "GeometricTransformation",
    "GeometricTransformation2D",
    "GeometricTransformation3D",
]
