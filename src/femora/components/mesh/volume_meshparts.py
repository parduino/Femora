import numpy as np
import pyvista as pv

from femora.core.element_base import Element
from femora.core.meshpart_base import MeshPart
from femora.core.region_base import RegionBase


class StructuredRectangular3D(MeshPart):
    _compatible_elements = ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]

    def __init__(
        self,
        user_name: str,
        element: Element,
        region: RegionBase | None = None,
        *,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        z_min: float,
        z_max: float,
        nx: int,
        ny: int,
        nz: int,
    ) -> None:
        super().__init__(
            category='volume mesh',
            mesh_type='Uniform Rectangular Grid',
            user_name=user_name,
            element=element,
            region=region,
        )
        self.x_min = float(x_min)
        self.x_max = float(x_max)
        self.y_min = float(y_min)
        self.y_max = float(y_max)
        self.z_min = float(z_min)
        self.z_max = float(z_max)
        self.nx = int(nx)
        self.ny = int(ny)
        self.nz = int(nz)

        if self.x_min >= self.x_max:
            raise ValueError("x_min must be less than x_max")
        if self.y_min >= self.y_max:
            raise ValueError("y_min must be less than y_max")
        if self.z_min >= self.z_max:
            raise ValueError("z_min must be less than z_max")
        if self.nx <= 0:
            raise ValueError("nx must be greater than 0")
        if self.ny <= 0:
            raise ValueError("ny must be greater than 0")
        if self.nz <= 0:
            raise ValueError("nz must be greater than 0")

        self.generate_mesh()

    def generate_mesh(self) -> pv.UnstructuredGrid:
        X = np.linspace(self.x_min, self.x_max, self.nx + 1)
        Y = np.linspace(self.y_min, self.y_max, self.ny + 1)
        Z = np.linspace(self.z_min, self.z_max, self.nz + 1)
        X, Y, Z = np.meshgrid(X, Y, Z, indexing='ij')
        self.mesh = pv.StructuredGrid(X, Y, Z).cast_to_unstructured_grid()
        return self.mesh

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        return element in cls._compatible_elements


class CustomRectangularGrid3D(MeshPart):
    _compatible_elements = ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]

    def __init__(
        self,
        user_name: str,
        element: Element,
        region: RegionBase | None = None,
        *,
        x_coords: str,
        y_coords: str,
        z_coords: str,
    ) -> None:
        super().__init__(
            category='volume mesh',
            mesh_type='Custom Rectangular Grid',
            user_name=user_name,
            element=element,
            region=region,
        )
        for param_name, value in (
            ("x_coords", x_coords),
            ("y_coords", y_coords),
            ("z_coords", z_coords),
        ):
            if not isinstance(value, str):
                raise TypeError(f"{param_name} must be a comma-separated string")
            try:
                coords = [float(x) for x in value.split(',')]
            except ValueError as exc:
                raise ValueError(f"{param_name} must be a list of float numbers") from exc
            if len(coords) < 2 or not all(coords[i] < coords[i + 1] for i in range(len(coords) - 1)):
                raise ValueError(f"{param_name} must contain at least two values in ascending order")
            setattr(self, param_name, coords)

        self.generate_mesh()

    def generate_mesh(self) -> pv.UnstructuredGrid:
        x = np.asarray(self.x_coords, dtype=float)
        y = np.asarray(self.y_coords, dtype=float)
        z = np.asarray(self.z_coords, dtype=float)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        self.mesh = pv.StructuredGrid(X, Y, Z).cast_to_unstructured_grid()
        return self.mesh

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        return element in cls._compatible_elements


class GeometricStructuredRectangular3D(MeshPart):
    _compatible_elements = ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]

    def __init__(
        self,
        user_name: str,
        element: Element,
        region: RegionBase | None = None,
        *,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        z_min: float,
        z_max: float,
        nx: int,
        ny: int,
        nz: int,
        x_ratio: float = 1.0,
        y_ratio: float = 1.0,
        z_ratio: float = 1.0,
    ) -> None:
        super().__init__(
            category='volume mesh',
            mesh_type='Geometric Rectangular Grid',
            user_name=user_name,
            element=element,
            region=region,
        )
        self.x_min = float(x_min)
        self.x_max = float(x_max)
        self.y_min = float(y_min)
        self.y_max = float(y_max)
        self.z_min = float(z_min)
        self.z_max = float(z_max)
        self.nx = int(nx)
        self.ny = int(ny)
        self.nz = int(nz)
        self.x_ratio = float(x_ratio)
        self.y_ratio = float(y_ratio)
        self.z_ratio = float(z_ratio)

        if self.x_min >= self.x_max:
            raise ValueError("x_min must be less than x_max")
        if self.y_min >= self.y_max:
            raise ValueError("y_min must be less than y_max")
        if self.z_min >= self.z_max:
            raise ValueError("z_min must be less than z_max")
        if self.nx <= 0:
            raise ValueError("nx must be greater than 0")
        if self.ny <= 0:
            raise ValueError("ny must be greater than 0")
        if self.nz <= 0:
            raise ValueError("nz must be greater than 0")
        for name, value in (
            ("x_ratio", self.x_ratio),
            ("y_ratio", self.y_ratio),
            ("z_ratio", self.z_ratio),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be greater than 0")

        self.generate_mesh()

    @staticmethod
    def custom_linspace(start, end, num_elements, ratio=1):
        if num_elements <= 0:
            raise ValueError("Number of elements must be greater than 0")

        if num_elements == 1:
            return np.array([start, end])

        num_intervals = num_elements
        total = end - start

        if ratio == 1:
            return np.linspace(start, end, num_elements + 1)

        x = total * (1 - ratio) / (1 - ratio**num_intervals)
        increments = x * (ratio ** np.arange(num_intervals))
        elements = start + np.cumsum(np.hstack([0, increments]))
        return elements

    def generate_mesh(self) -> pv.UnstructuredGrid:
        x = self.custom_linspace(self.x_min, self.x_max, self.nx, self.x_ratio)
        y = self.custom_linspace(self.y_min, self.y_max, self.ny, self.y_ratio)
        z = self.custom_linspace(self.z_min, self.z_max, self.nz, self.z_ratio)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        self.mesh = pv.StructuredGrid(X, Y, Z).cast_to_unstructured_grid()
        return self.mesh

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        return element in cls._compatible_elements
