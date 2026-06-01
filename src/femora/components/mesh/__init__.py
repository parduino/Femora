"""---
icon: material/grid
---

Mesh-part component package for Femora.

This package contains concrete mesh-part component classes representing lines, surfaces,
volumes, and composite/external structures in an OpenSees analysis. These mesh parts define
the geometric shapes, discretization (grid sizing/spacing), associated element typologies,
and physical regions.

Normal runtime usage should go through `Model` manager entry points under the
`model.meshpart` namespace (e.g., `model.meshpart.line.*`, `model.meshpart.volume.*`,
`model.meshpart.surface.*`, and `model.meshpart.general.*`). Direct imports from this
package are mainly useful for typed references, tests, and low-level component work.
"""

from femora.components.mesh.volume_meshparts import (
    CustomRectangularGrid3D,
    GeometricStructuredRectangular3D,
    StructuredRectangular3D,
)
from femora.components.mesh.line_meshparts import SingleLineMesh, StructuredLineMesh
from femora.components.mesh.surface_meshparts import CircularOGrid2D
from femora.components.mesh.general_meshparts import CompositeMesh, ExternalMesh

__all__ = [
    "StructuredRectangular3D",
    "CustomRectangularGrid3D",
    "GeometricStructuredRectangular3D",
    "SingleLineMesh",
    "StructuredLineMesh",
    "CircularOGrid2D",
    "ExternalMesh",
    "CompositeMesh",
]
