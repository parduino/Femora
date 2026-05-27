"""Continuum nD material components for Femora.

This subpackage contains ``nDMaterial`` component classes used with continuum
elements such as bricks and quads. The classes wrap OpenSees models ranging
from linear elasticity and modulus-degradation curves to pressure-sensitive
and multi-yield soil plasticity.

Normal runtime usage should go through
``model.material.nd.<factory>(...)`` on a [Model][femora.core.model.Model]
instance, for example ``model.material.nd.elastic_isotropic(...)`` or
``model.material.nd.pressure_depend_multi_yield(...)``. Direct imports from
this subpackage are mainly useful for typed references and tests.
"""

from femora.components.material.nd.drucker_prager import DruckerPragerMaterial
from femora.components.material.nd.elastic_isotropic import ElasticIsotropicMaterial
from femora.components.material.nd.j2_cyclic_bounding_surface import (
    J2CyclicBoundingSurfaceMaterial,
)
from femora.components.material.nd.linear_elastic_ggmax import LinearElasticGGmaxMaterial
from femora.components.material.nd.pressure_depend_multi_yield import (
    PressureDependMultiYieldMaterial,
)
from femora.components.material.nd.pressure_independ_multi_yield import (
    PressureIndependMultiYieldMaterial,
)

__all__ = [
    "DruckerPragerMaterial",
    "ElasticIsotropicMaterial",
    "J2CyclicBoundingSurfaceMaterial",
    "LinearElasticGGmaxMaterial",
    "PressureDependMultiYieldMaterial",
    "PressureIndependMultiYieldMaterial",
]
