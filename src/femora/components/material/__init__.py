"""---
icon: material/atom-variant
---

Material component package for Femora.

This package contains runtime material component classes that are registered
through [MaterialManager][femora.core.material_manager.MaterialManager] and
exported to OpenSees Tcl as ``nDMaterial`` or ``uniaxialMaterial`` commands.

Normal runtime usage should go through a [Model][femora.core.model.Model]
instance and its material manager entry points, such as
``model.material.nd.*`` and ``model.material.uniaxial.*``. Direct imports from
this package are mainly useful for typed references, tests, and low-level
component work.

This package includes:
- [femora.components.material.nd][]: continuum nD materials for solid elements
- [femora.components.material.uniaxial][]: uniaxial materials for truss,
  spring, and fiber models
"""

from femora.components.material.nd import (
    DruckerPragerMaterial,
    ElasticIsotropicMaterial,
    J2CyclicBoundingSurfaceMaterial,
    LinearElasticGGmaxMaterial,
    PressureDependMultiYieldMaterial,
    PressureIndependMultiYieldMaterial,
)
from femora.components.material.uniaxial import (
    ElasticUniaxialMaterial,
    Steel01Material,
)

__all__ = [
    "DruckerPragerMaterial",
    "ElasticIsotropicMaterial",
    "ElasticUniaxialMaterial",
    "J2CyclicBoundingSurfaceMaterial",
    "LinearElasticGGmaxMaterial",
    "PressureDependMultiYieldMaterial",
    "PressureIndependMultiYieldMaterial",
    "Steel01Material",
]
