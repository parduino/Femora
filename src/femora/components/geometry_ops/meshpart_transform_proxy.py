from __future__ import annotations

from typing import Optional, Sequence, Union, Any

import pyvista as pv

from .spatial_transform_manager import SpatialTransformManager


class MeshPartTransform:
    """
    Per-instance transform proxy bound to a MeshPart.

    Usage: meshpart.transform.rotate_z(30.0, point=meshpart.mesh.center)
    """

    def __init__(self, meshpart: Any) -> None:
        # Typed as Any to avoid circular typing imports
        self._meshpart = meshpart
        self._ops = SpatialTransformManager()

    def translate(self, vector: Sequence[float], *, multiply_mode: str = "pre", inplace: bool = True):
        return self._ops.translate(self._meshpart, vector, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def rotate(self, rotation: Union[Sequence[Sequence[float]], Sequence[float]], *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        return self._ops.rotate(self._meshpart, rotation, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def rotate_vector(self, vector: Sequence[float], angle: float, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        return self._ops.rotate_vector(self._meshpart, vector, angle, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def rotate_x(self, angle: float, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        return self._ops.rotate_x(self._meshpart, angle, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def rotate_y(self, angle: float, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        return self._ops.rotate_y(self._meshpart, angle, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def rotate_z(self, angle: float, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        return self._ops.rotate_z(self._meshpart, angle, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def scale(self, factor: Union[float, Sequence[float]], *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        return self._ops.scale(self._meshpart, factor, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def flip_x(self, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        return self._ops.flip_x(self._meshpart, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def flip_y(self, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        return self._ops.flip_y(self._meshpart, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def flip_z(self, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        return self._ops.flip_z(self._meshpart, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def reflect(self, normal: Sequence[float], *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        return self._ops.reflect(self._meshpart, normal, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def apply_transform(self, transform: pv.transform.Transform, *, inplace: bool = True):
        return self._ops.apply_transform(self._meshpart, transform, cascade=False, inplace=inplace)


__all__ = ["MeshPartTransform"]


