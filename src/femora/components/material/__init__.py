"""Concrete OpenSees materials bound to :class:`~femora.core.material_manager.MaterialManager`.

Runtime code should normally create instances via ``manager.nd.*`` /
``manager.uniaxial.*``.  Direct imports from this package are supported for typed
references and tests.

Subpackages organize materials by dimensionality/type:

    * :mod:`femora.components.material.nd`
    * :mod:`femora.components.material.uniaxial`
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
