from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class Material(ABC):
    """Abstract base class for manager-owned OpenSees material objects.

    Material instances do not self-register and do not assign their own tags.
    A :class:`~femora.core.material_manager.MaterialManager` owns lifecycle
    operations, tag assignment, removal, and retagging for a local model context.

    Args:
        material_type: OpenSees material category (e.g. ``'nDMaterial'``).
        material_name: Concrete OpenSees material name (e.g. ``'ElasticIsotropic'``).
        user_name: User-specified label for this material instance.

    Attributes:
        tag: Manager-assigned OpenSees material tag.  Remains ``None`` until
            this object is added to a :class:`~femora.core.material_manager.MaterialManager`.
        _owner: Reference to the owning manager, or ``None`` when unmanaged.
    """

    def __init__(self, material_type: str, material_name: str, user_name: str):
        self.tag: Optional[int] = None
        self._owner: object | None = None
        self.material_type = material_type
        self.material_name = material_name
        self.user_name = user_name
        self.params: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Tag helpers
    # ------------------------------------------------------------------

    def _require_tag(self) -> int:
        """Return the assigned tag, or raise if this material is unmanaged."""
        if self.tag is None:
            raise ValueError(
                f"Material '{self.user_name}' must be added to a MaterialManager "
                "before rendering TCL."
            )
        return self.tag

    @abstractmethod
    def to_tcl(self) -> str:
        """Render the OpenSees material definition command as a Tcl string."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Optional overrides
    # ------------------------------------------------------------------

    def updateMaterialStage(self, state: str) -> str:
        """Return an ``updateMaterialStage`` Tcl command, or empty string."""
        return ""

    def set_parameter(
        self,
        parameter_name: str,
        new_value: Union[float, int, str, None] = None,
        element_tags: Optional[List[int]] = None,
    ) -> str:
        """Return a ``setParameter`` Tcl command, or empty string."""
        return ""

    def get_param(self, key: str) -> Any:
        """Return the value of a stored parameter by key."""
        return self.params[key]

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"tag={self.tag}, "
            f"type={self.material_type}, "
            f"name={self.material_name}, "
            f"user_name={self.user_name!r})"
        )

    def __str__(self) -> str:
        tag = self.tag if self.tag is not None else "unmanaged"
        return (
            f"{self.material_type} {self.material_name} "
            f"(Tag: {tag}, user_name: {self.user_name!r})"
        )


__all__ = ["Material"]
