# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class GeometricTransformation(ABC):
    """Abstract base class for OpenSees geometric transformations.

    Transformation instances do not self-register and do not assign their own
    tags. A :class:`TransformationManager` owns lifecycle operations, tag
    assignment, removal, and retagging for a local model context.

    Args:
        transf_type: OpenSees geometric transformation type.
        dimension: Spatial dimension, either ``2`` or ``3``.
        description: Optional comment appended to the rendered Tcl command.

    Attributes:
        tag: Manager-assigned OpenSees transformation tag. It remains ``None``
            until this object is added to a ``TransformationManager``.
    """

    eps = 1e-12

    def __init__(self, transf_type: str, dimension: int, description: str = ""):
        if not isinstance(transf_type, str) or not transf_type.strip():
            raise ValueError("transf_type must be a non-empty string")
        dimension = int(dimension)
        if dimension not in (2, 3):
            raise ValueError("dimension must be 2 or 3")

        self.tag: Optional[int] = None
        self._owner: object | None = None
        self._transformation_type = transf_type
        self._dimension = dimension
        self.description = description

    @property
    def transformation_type(self) -> str:
        return self._transformation_type

    @property
    def dimension(self) -> int:
        return self._dimension

    def _require_tag(self) -> int:
        """Return the assigned tag or fail if the transformation is unmanaged."""
        if self.tag is None:
            raise ValueError("GeometricTransformation must be managed before rendering TCL")
        return self.tag

    @abstractmethod
    def has_joint_offsets(self) -> bool:
        """Return whether the transformation has nonzero joint offsets."""
        raise NotImplementedError

    @abstractmethod
    def to_tcl(self) -> str:
        """Render the OpenSees ``geomTransf`` command."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(tag={self.tag}, type={self.transformation_type})"

    def __str__(self) -> str:
        tag = self.tag if self.tag is not None else "unmanaged"
        return f"{self.transformation_type} {self.dimension}D Transformation (Tag: {tag})"
