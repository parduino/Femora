# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Iterator, Optional

from femora.components.transformation.transformation import (
    GeometricTransformation2D,
    GeometricTransformation3D,
)
from femora.core.tagging import CompactRetagPolicy
from femora.core.transformation_base import GeometricTransformation

if TYPE_CHECKING:
    from femora.core.model import Model


class TransformationManager:
    """Local manager for geometric transformation lifecycle and tag assignment."""

    def __init__(self, mesh_maker: Model):
        """Create an empty transformation manager with tags starting at ``1``."""
        from femora.core.model import Model as ModelClass

        if not isinstance(mesh_maker, ModelClass):
            raise TypeError("mesh_maker must be a Model instance")
        existing_manager = getattr(mesh_maker, "transformation", None)
        if isinstance(existing_manager, TransformationManager):
            raise ValueError("mesh_maker already owns a transformation manager")
        self._mesh_maker = mesh_maker
        self._transformations: Dict[int, GeometricTransformation] = {}
        self._start_tag = 1
        self._tagging = CompactRetagPolicy[GeometricTransformation]()

    def __len__(self) -> int:
        """Return the number of managed transformations."""
        return len(self._transformations)

    def __iter__(self) -> Iterator[GeometricTransformation]:
        """Iterate over managed transformations in tag order."""
        return iter(self._transformations.values())

    def add(self, transformation: GeometricTransformation) -> GeometricTransformation:
        """Add an existing transformation and assign a tag if needed.

        Args:
            transformation: Unmanaged or already-managed transformation.

        Returns:
            The same transformation after it is stored by this manager.
        """
        if not isinstance(transformation, GeometricTransformation):
            raise TypeError("transformation must be a GeometricTransformation instance")
        if transformation._owner is None:
            transformation._owner = self
        elif transformation._owner is not self:
            raise ValueError("transformation already belongs to another manager")

        try:
            transformation.tag = self._tagging.assign_tag(
                self._transformations,
                transformation,
                self._start_tag,
            )
        except ValueError as exc:
            raise ValueError(f"Transformation tag {transformation.tag} already exists") from exc
        self._transformations[transformation.tag] = transformation
        return transformation

    def get(self, tag: int) -> Optional[GeometricTransformation]:
        """Return the transformation with ``tag`` if it exists."""
        return self._transformations.get(int(tag))

    def get_all(self) -> Dict[int, GeometricTransformation]:
        """Return a shallow copy of all managed transformations keyed by tag."""
        return dict(self._transformations)

    def remove(self, tag: int) -> None:
        """Remove a managed transformation and compact the remaining tags."""
        transformation = self._transformations.pop(int(tag), None)
        if transformation is not None:
            transformation.tag = None
            transformation._owner = None
            self._reassign_tags()

    def clear(self) -> None:
        """Remove all transformations and clear their assigned tags."""
        for transformation in self._transformations.values():
            transformation.tag = None
            transformation._owner = None
        self._transformations.clear()

    def set_tag_start(self, start_tag: int) -> None:
        """Set the first tag used by this manager and retag existing objects."""
        self._start_tag = self._tagging.validate_start_tag(start_tag)
        self._reassign_tags()

    def transformation2d(
        self,
        transf_type: str,
        d_xi: float = 0.0,
        d_yi: float = 0.0,
        d_xj: float = 0.0,
        d_yj: float = 0.0,
        description: str = "",
    ) -> GeometricTransformation2D:
        """Create and manage a 2D geometric transformation."""
        return self.add(
            GeometricTransformation2D(
                transf_type=transf_type,
                d_xi=d_xi,
                d_yi=d_yi,
                d_xj=d_xj,
                d_yj=d_yj,
                description=description,
            )
        )  # type: ignore[return-value]

    def transformation3d(
        self,
        transf_type: str,
        vecxz_x: float | str,
        vecxz_y: float | str,
        vecxz_z: float | str,
        d_xi: float | str = 0.0,
        d_yi: float | str = 0.0,
        d_zi: float | str = 0.0,
        d_xj: float | str = 0.0,
        d_yj: float | str = 0.0,
        d_zj: float | str = 0.0,
        description: str = "",
    ) -> GeometricTransformation3D:
        """Create and manage a 3D geometric transformation."""
        return self.add(
            GeometricTransformation3D(
                transf_type=transf_type,
                vecxz_x=vecxz_x,
                vecxz_y=vecxz_y,
                vecxz_z=vecxz_z,
                d_xi=d_xi,
                d_yi=d_yi,
                d_zi=d_zi,
                d_xj=d_xj,
                d_yj=d_yj,
                d_zj=d_zj,
                description=description,
            )
        )  # type: ignore[return-value]

    def _next_available_tag(self) -> int:
        """Return the next unused tag in this manager's local tag space."""
        return self._tagging.next_available_tag(self._transformations, self._start_tag)

    def _reassign_tags(self) -> None:
        """Retag all managed transformations from ``_start_tag`` in tag order."""
        self._tagging.reassign_tags(self._transformations, self._start_tag)

__all__ = [
    "TransformationManager",
    "GeometricTransformation",
    "GeometricTransformation2D",
    "GeometricTransformation3D",
]
