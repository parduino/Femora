from __future__ import annotations

from femora.components.material.nd import (
    DruckerPragerMaterial,
    ElasticIsotropicMaterial,
    J2CyclicBoundingSurfaceMaterial,
    LinearElasticGGmaxMaterial,
    PressureDependMultiYieldMaterial,
    PressureIndependMultiYieldMaterial,
)


class NDMaterialManager:
    """Bound factory namespace for nD material creation."""

    def __init__(self, manager):
        self._manager = manager

    @staticmethod
    def _normalize_user_name(kwargs):
        if "name" in kwargs:
            if "user_name" in kwargs:
                raise TypeError("Use only one of 'name' or 'user_name'")
            kwargs["user_name"] = kwargs.pop("name")
        return kwargs

    def elastic_isotropic(
        self,
        user_name: str = "Unnamed",
        E: float = 1.0,
        nu: float = 0.3,
        rho: float = 0.0,
        **kwargs,
    ):
        kwargs = self._normalize_user_name(kwargs)
        return self._manager.add(
            ElasticIsotropicMaterial(
                user_name=kwargs.pop("user_name", user_name),
                E=E,
                nu=nu,
                rho=rho,
            )
        )

    def j2_cyclic_bounding_surface(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self._normalize_user_name(kwargs)
        return self._manager.add(
            J2CyclicBoundingSurfaceMaterial(
                user_name=kwargs.pop("user_name", user_name),
                **kwargs,
            )
        )

    def drucker_prager(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self._normalize_user_name(kwargs)
        return self._manager.add(
            DruckerPragerMaterial(
                user_name=kwargs.pop("user_name", user_name),
                **kwargs,
            )
        )

    def pressure_depend_multi_yield(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self._normalize_user_name(kwargs)
        return self._manager.add(
            PressureDependMultiYieldMaterial(
                user_name=kwargs.pop("user_name", user_name),
                **kwargs,
            )
        )

    def linear_elastic_ggmax(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self._normalize_user_name(kwargs)
        return self._manager.add(
            LinearElasticGGmaxMaterial(
                user_name=kwargs.pop("user_name", user_name),
                **kwargs,
            )
        )

    def pressure_independ_multi_yield(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self._normalize_user_name(kwargs)
        return self._manager.add(
            PressureIndependMultiYieldMaterial(
                user_name=kwargs.pop("user_name", user_name),
                **kwargs,
            )
        )


__all__ = ["NDMaterialManager"]
