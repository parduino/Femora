
# Only references to the relevant material classes, no management methods
from .materialsOpenSees import (
    ElasticIsotropicMaterial,
    J2CyclicBoundingSurfaceMaterial,
    DruckerPragerMaterial,
    PressureDependMultiYieldMaterial,
    ElasticUniaxialMaterial,
    Steel01Material,
)

class NDMaterialManager:
    elastic_isotropic = ElasticIsotropicMaterial
    j2_cyclic_bounding_surface = J2CyclicBoundingSurfaceMaterial
    drucker_prager = DruckerPragerMaterial
    pressure_depend_multi_yield = PressureDependMultiYieldMaterial
    

class UniaxialMaterialManager:
    elastic = ElasticUniaxialMaterial
    steel01 = Steel01Material
