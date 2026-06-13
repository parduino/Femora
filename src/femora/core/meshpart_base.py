# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Type

import numpy as np
import pyvista as pv

from femora.components.geometry_ops import MeshPartTransform
from femora.constants import FEMORA_MAX_NDF
from femora.core.damping_base import Damping
from femora.core.element_base import Element
from femora.core.region_base import RegionBase


class MeshPart(ABC):
    """Base class for mesh parts on one Model model.

    Instances do not self-register. A :class:`MeshPartManager` owns tag
    assignment and lifecycle.
    """

    _compatible_elements: list = []

    def __init__(
        self,
        category: str,
        mesh_type: str,
        user_name: str,
        element: Optional[Element],
        region: Optional[RegionBase] = None,
    ) -> None:
        self.category = category
        self.mesh_type = mesh_type
        self.user_name = user_name
        self.element = element
        self.region = region
        self.mesh: Optional[pv.DataSet] = None
        self.actor = None
        self.transform = MeshPartTransform(self)
        self.tag: Optional[int] = None
        self._owner: Optional[object] = None

    @abstractmethod
    def generate_mesh(self) -> None:
        pass

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        return element.lower() in [e.lower() for e in cls._compatible_elements]

    def assign_material(self, material) -> None:
        if self.element is None:
            raise ValueError("No element to assign material to")
        if self.element.material is not None:
            self.element.assign_material(material)
        else:
            raise ValueError("No material to assign to the element")

    def assign_actor(self, actor) -> None:
        self.actor = actor

    def _ensure_mass_array(self) -> None:
        if self.mesh is None:
            return
        if "Mass" not in self.mesh.point_data:
            n_pts = self.mesh.n_points
            self.mesh.point_data["Mass"] = np.zeros((n_pts, FEMORA_MAX_NDF), dtype=np.float32)

    def plot(self, off_screen: bool = False, screenshot: Optional[str] = None, **kwargs) -> None:
        if self.mesh is None:
            raise ValueError("Mesh not generated yet. Call generate_mesh() first.")
        self._ensure_mass_array()
        plotter = pv.Plotter(off_screen=off_screen)
        plotter.add_mesh(self.mesh, **kwargs)
        plotter.show(screenshot=screenshot)

    def set_damping(self, damping_instance: Type[Damping]):
        if self.region is None:
            raise ValueError("No region available to assign damping to.")
        self.region.set_damping(damping_instance)


__all__ = ["MeshPart"]
