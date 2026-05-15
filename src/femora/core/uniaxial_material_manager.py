from __future__ import annotations

from femora.components.material.uniaxial import (
    ElasticUniaxialMaterial,
    Steel01Material,
)


class UniaxialMaterialManager:
    """Bound factory namespace for uniaxial material creation."""

    def __init__(self, manager):
        self._manager = manager

    @staticmethod
    def _normalize_user_name(kwargs):
        if "name" in kwargs:
            if "user_name" in kwargs:
                raise TypeError("Use only one of 'name' or 'user_name'")
            kwargs["user_name"] = kwargs.pop("name")
        return kwargs

    def elastic(
        self,
        user_name: str = "Unnamed",
        E: float = 1.0,
        eta: float = 0.0,
        Eneg: float | None = None,
        **kwargs,
    ):
        kwargs = self._normalize_user_name(kwargs)
        params = dict(E=E, eta=eta)
        if Eneg is not None:
            params["Eneg"] = Eneg
        return self._manager.add(
            ElasticUniaxialMaterial(
                user_name=kwargs.pop("user_name", user_name),
                **params,
            )
        )

    def steel01(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self._normalize_user_name(kwargs)
        return self._manager.add(
            Steel01Material(
                user_name=kwargs.pop("user_name", user_name),
                **kwargs,
            )
        )


__all__ = ["UniaxialMaterialManager"]
