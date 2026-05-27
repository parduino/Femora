import numpy as np
import pyvista as pv

from femora.core.element_base import Element
from femora.core.meshpart_base import MeshPart
from femora.core.region_base import RegionBase


class StructuredRectangular3D(MeshPart):
    """Parametric structured uniform 3D rectangular mesh part.

    This mesh part discretizes a 3D rectangular bounding box defined by boundaries
    along the X, Y, and Z coordinate axes into a uniform grid of 3D solid elements
    (such as `stdBrick`, `SSPbrick`, or `PML3D`).

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        mat = model.material.nd.elastic_isotropic(user_name="soil", e_mod=30000.0, nu=0.3, rho=2.0)
        ele = model.element.brick.std(ndof=3, material=mat)

        # Discretize a 10x10x10 uniform 3D grid block
        block = model.meshpart.volume.uniform_rectangular_grid(
            user_name="soil_block",
            element=ele,
            x_min=0.0, x_max=10.0,
            y_min=0.0, y_max=10.0,
            z_min=0.0, z_max=10.0,
            nx=5, ny=5, nz=5,
        )
        print(block.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "generate_mesh"],
    }

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
        """Create a parametric structured uniform 3D rectangular mesh part.

        Args:
            user_name: Unique user-defined name for this mesh part.
            element: Associated Element template used for discretization.
            region: Physical Region where this mesh part is added.
            x_min: Minimum X-coordinate bounding value.
            x_max: Maximum X-coordinate bounding value.
            y_min: Minimum Y-coordinate bounding value.
            y_max: Maximum Y-coordinate bounding value.
            z_min: Minimum Z-coordinate bounding value.
            z_max: Maximum Z-coordinate bounding value.
            nx: Number of element subdivisions along the X-axis (must be greater than 0).
            ny: Number of element subdivisions along the Y-axis (must be greater than 0).
            nz: Number of element subdivisions along the Z-axis (must be greater than 0).

        Raises:
            ValueError: If min bounding coordinates are not less than max bounding coordinates,
                or if cell subdivision counts are less than or equal to 0.
        """
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
        """Calculate structured uniform grid coordinates and cast to UnstructuredGrid.

        Returns:
            pv.UnstructuredGrid: The generated uniform UnstructuredGrid mesh.
        """
        X = np.linspace(self.x_min, self.x_max, self.nx + 1)
        Y = np.linspace(self.y_min, self.y_max, self.ny + 1)
        Z = np.linspace(self.z_min, self.z_max, self.nz + 1)
        X, Y, Z = np.meshgrid(X, Y, Z, indexing='ij')
        self.mesh = pv.StructuredGrid(X, Y, Z).cast_to_unstructured_grid()
        return self.mesh

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        """Check if the given element type is compatible with 3D volume meshes.

        Args:
            element: Type name of the element.

        Returns:
            bool: True if compatible, False otherwise.
        """
        return element in cls._compatible_elements


class CustomRectangularGrid3D(MeshPart):
    """Custom 3D rectangular mesh part discretized using comma-separated coordinates list strings.

    This mesh part defines a 3D rectangular solid grid with customized element spacing.
    The node spacing along the X, Y, and Z axes is defined directly via lists of coordinates
    supplied as comma-separated string inputs.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        mat = model.material.nd.elastic_isotropic(user_name="soil", e_mod=30000.0, nu=0.3, rho=2.0)
        ele = model.element.brick.std(ndof=3, material=mat)

        # Discretize a 3D grid with refinement near the origin
        block = model.meshpart.volume.custom_rectangular_grid(
            user_name="refined_block",
            element=ele,
            x_coords="0.0,1.0,3.0,6.0,10.0",
            y_coords="0.0,1.0,3.0,6.0,10.0",
            z_coords="0.0,2.0,5.0,10.0",
        )
        print(block.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "generate_mesh"],
    }

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
        """Create a custom-discretized 3D rectangular grid mesh part.

        Args:
            user_name: Unique user-defined name for this mesh part.
            element: Associated Element template used for discretization.
            region: Physical Region where this mesh part is added.
            x_coords: Comma-separated floats representing X-coordinate positions in ascending order.
            y_coords: Comma-separated floats representing Y-coordinate positions in ascending order.
            z_coords: Comma-separated floats representing Z-coordinate positions in ascending order.

        Raises:
            TypeError: If coordinates inputs are not string types.
            ValueError: If coordinate lists contain fewer than two coordinates,
                if coordinates fail to parse, or are not in strictly ascending order.
        """
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
        """Calculate custom grid coordinates and compile a PyVista UnstructuredGrid.

        Returns:
            pv.UnstructuredGrid: The generated custom UnstructuredGrid mesh.
        """
        x = np.asarray(self.x_coords, dtype=float)
        y = np.asarray(self.y_coords, dtype=float)
        z = np.asarray(self.z_coords, dtype=float)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        self.mesh = pv.StructuredGrid(X, Y, Z).cast_to_unstructured_grid()
        return self.mesh

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        """Check if the given element type is compatible with 3D volume meshes.

        Args:
            element: Type name of the element.

        Returns:
            bool: True if compatible, False otherwise.
        """
        return element in cls._compatible_elements


class GeometricStructuredRectangular3D(MeshPart):
    """Parametric structured 3D rectangular mesh part with geometric grid expansion.

    This mesh part discretizes a 3D rectangular box using geometric spacing ratios
    along the coordinate axes. Node coordinates along each axis are generated in a
    geometric progression, which is highly useful for soil-foundation interfaces requiring
    refinement near structural elements and coarse spacing far away.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        mat = model.material.nd.elastic_isotropic(user_name="soil", e_mod=30000.0, nu=0.3, rho=2.0)
        ele = model.element.brick.std(ndof=3, material=mat)

        # Discretize a 3D grid with geometric expansion along the Z-axis
        block = model.meshpart.volume.geometric_rectangular_grid(
            user_name="soil_block_geom",
            element=ele,
            x_min=0.0, x_max=10.0,
            y_min=0.0, y_max=10.0,
            z_min=0.0, z_max=20.0,
            nx=5, ny=5, nz=8,
            z_ratio=1.2,
        )
        print(block.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "generate_mesh"],
    }

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
        """Create a structured geometrically-spaced 3D rectangular mesh part.

        Args:
            user_name: Unique user-defined name for this mesh part.
            element: Associated Element template used for discretization.
            region: Physical Region where this mesh part is added.
            x_min: Minimum X-coordinate bounding value.
            x_max: Maximum X-coordinate bounding value.
            y_min: Minimum Y-coordinate bounding value.
            y_max: Maximum Y-coordinate bounding value.
            z_min: Minimum Z-coordinate bounding value.
            z_max: Maximum Z-coordinate bounding value.
            nx: Number of element subdivisions along the X-axis (must be greater than 0).
            ny: Number of element subdivisions along the Y-axis (must be greater than 0).
            nz: Number of element subdivisions along the Z-axis (must be greater than 0).
            x_ratio: Geometric spacing ratio along the X-axis (must be greater than 0).
            y_ratio: Geometric spacing ratio along the Y-axis (must be greater than 0).
            z_ratio: Geometric spacing ratio along the Z-axis (must be greater than 0).

        Raises:
            ValueError: If min bounding coordinates are not less than max bounding coordinates,
                if cell subdivision counts are less than or equal to 0, or if geometric ratios
                are less than or equal to 0.
        """
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
    def custom_linspace(start: float, end: float, num_elements: int, ratio: float = 1.0) -> np.ndarray:
        """Generate a geometric progression sequence between start and end.

        Args:
            start: Start coordinate.
            end: End coordinate.
            num_elements: Number of elements (intervals).
            ratio: Geometric ratio between consecutive spacing intervals.

        Returns:
            np.ndarray: Array of generated coordinate positions.

        Raises:
            ValueError: If num_elements is less than or equal to 0.
        """
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
        """Generate geometrically-spaced structured grid coordinates and cast to UnstructuredGrid.

        Returns:
            pv.UnstructuredGrid: The generated geometrically structured UnstructuredGrid mesh.
        """
        x = self.custom_linspace(self.x_min, self.x_max, self.nx, self.x_ratio)
        y = self.custom_linspace(self.y_min, self.y_max, self.ny, self.y_ratio)
        z = self.custom_linspace(self.z_min, self.z_max, self.nz, self.z_ratio)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        self.mesh = pv.StructuredGrid(X, Y, Z).cast_to_unstructured_grid()
        return self.mesh

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        """Check if the given element type is compatible with 3D volume meshes.

        Args:
            element: Type name of the element.

        Returns:
            bool: True if compatible, False otherwise.
        """
        return element in cls._compatible_elements
