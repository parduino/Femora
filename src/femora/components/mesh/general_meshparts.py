import os
from typing import Optional

import pyvista as pv

from femora.core.element_base import Element
from femora.core.material_base import Material
from femora.core.meshpart_base import MeshPart
from femora.core.region_base import RegionBase


class ExternalMesh(MeshPart):
    _compatible_elements = ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]

    def __init__(
        self,
        user_name: str,
        element: Element,
        region: RegionBase | None = None,
        *,
        mesh: pv.DataSet | None = None,
        filepath: str | None = None,
        scale: float | None = None,
        rotate_x: float | None = None,
        rotate_y: float | None = None,
        rotate_z: float | None = None,
        translate_x: float = 0.0,
        translate_y: float = 0.0,
        translate_z: float = 0.0,
    ) -> None:
        super().__init__(
            category='volume mesh',
            mesh_type='Custom Mesh',
            user_name=user_name,
            element=element,
            region=region,
        )

        if mesh is not None and filepath is not None:
            raise ValueError("Provide either mesh or filepath, not both")
        if mesh is None and filepath is None:
            raise ValueError("Either mesh or filepath is required")

        if mesh is not None:
            if not isinstance(mesh, (pv.UnstructuredGrid, pv.PolyData, pv.StructuredGrid)):
                raise TypeError("mesh must be a PyVista mesh")
            self.source_mesh = mesh
            self.filepath = None
        else:
            if not isinstance(filepath, str):
                raise TypeError("filepath must be a string")
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Mesh file not found: {filepath}")
            self.filepath = filepath
            self.source_mesh = None

        self.scale = float(scale) if scale is not None else None
        self.rotate_x = float(rotate_x) if rotate_x is not None else None
        self.rotate_y = float(rotate_y) if rotate_y is not None else None
        self.rotate_z = float(rotate_z) if rotate_z is not None else None
        self.translate_x = float(translate_x)
        self.translate_y = float(translate_y)
        self.translate_z = float(translate_z)

        if self.scale is not None and self.scale <= 0:
            raise ValueError("scale must be greater than 0")

        self.generate_mesh()

    def generate_mesh(self) -> pv.UnstructuredGrid:
        if self.source_mesh is not None:
            self.mesh = self.source_mesh
        else:
            self.mesh = pv.read(self.filepath)

        if self.scale is not None:
            self.mesh.scale(self.scale, inplace=True)

        if self.rotate_x is not None:
            self.mesh.rotate_x(self.rotate_x, inplace=True)
        if self.rotate_y is not None:
            self.mesh.rotate_y(self.rotate_y, inplace=True)
        if self.rotate_z is not None:
            self.mesh.rotate_z(self.rotate_z, inplace=True)

        if self.translate_x != 0 or self.translate_y != 0 or self.translate_z != 0:
            self.mesh.translate(
                [self.translate_x, self.translate_y, self.translate_z],
                inplace=True,
            )

        if not isinstance(self.mesh, pv.UnstructuredGrid):
            try:
                self.mesh = self.mesh.cast_to_unstructured_grid()
            except Exception as e:
                raise ValueError(f"Failed to convert mesh to unstructured grid: {str(e)}") from e

        return self.mesh

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        return element in cls._compatible_elements


class CompositeMesh(MeshPart):
    _compatible_elements = ["variable"]

    def __init__(
        self,
        user_name: str,
        mesh: pv.UnstructuredGrid,
        region: RegionBase | None = None,
        *,
        ndof: int = 6,
        element_tag: int = 0,
        material_tag: int = 0,
        section_tag: int = 0,
    ) -> None:
        super().__init__(
            category='structure',
            mesh_type='Composite Mesh',
            user_name=user_name,
            element=None,
            region=region,
        )
        if not isinstance(mesh, pv.UnstructuredGrid):
            raise TypeError("mesh must be a pyvista UnstructuredGrid")
        self.mesh = mesh
        self.ndof = int(ndof)
        self.element_tag = int(element_tag)
        self.material_tag = int(material_tag)
        self.section_tag = int(section_tag)
        self._ensure_mass_array()

    def generate_mesh(self) -> pv.UnstructuredGrid:
        return self.mesh

    def assign_material(self, material: Material) -> None:
        pass

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        return True
