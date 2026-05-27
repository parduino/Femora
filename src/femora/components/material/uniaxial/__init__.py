"""Uniaxial material components for Femora.

This subpackage contains ``uniaxialMaterial`` component classes used for
springs, fibers, truss-style response, and other one-dimensional constitutive
behavior in OpenSees models.

Normal runtime usage should go through
``model.material.uniaxial.<factory>(...)`` on a
[Model][femora.core.model.Model] instance, which creates and registers these
materials under the owning material manager. Direct imports from this
subpackage are mainly useful for typed references and tests.
"""

from femora.components.material.uniaxial.elastic import ElasticUniaxialMaterial
from femora.components.material.uniaxial.steel01 import Steel01Material

__all__ = [
    "ElasticUniaxialMaterial",
    "Steel01Material",
]
