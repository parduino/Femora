
# Only references to the relevant material classes, no management methods
from .materialsOpenSees import ElasticIsotropicMaterial, J2CyclicBoundingSurfaceMaterial, DruckerPragerMaterial, ElasticUniaxialMaterial

class NDMaterialManager:
    elastic_isotropic = ElasticIsotropicMaterial
    j2_cyclic_bounding_surface = J2CyclicBoundingSurfaceMaterial
    drucker_prager = DruckerPragerMaterial
    

class UniaxialMaterialManager:
    elastic = ElasticUniaxialMaterial
