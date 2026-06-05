import os
from typing import Optional

import pyvista as pv

from femora.core.element_base import Element
from femora.core.material_base import Material
from femora.core.meshpart_base import MeshPart
from femora.core.region_base import RegionBase


class ExternalMesh(MeshPart):
    """PyVista-based custom volume mesh part imported from an external file or dataset.

    This mesh part allows importing custom 3D volume meshes (such as VTK, VTU, or OBJ files)
    via PyVista. It supports scale, rotation, and translation transformations, casting the
    source mesh to a PyVista UnstructuredGrid for use with 3D brick or PML elements.

    Note:
        - Provide either `mesh` (a pre-loaded PyVista DataSet) or `filepath` (path to a mesh file on disk), but not both.
        - The imported mesh is automatically cast to a PyVista UnstructuredGrid format required by Femora.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        mat = model.material.nd.elastic_isotropic(user_name="soil", e_mod=30000.0, nu=0.3, rho=2.0)
        ele = model.element.brick.std(ndof=3, material=mat)

        # Create an external mesh part via filepath
        mesh_part = model.meshpart.general.external_mesh(
            user_name="ext_soil",
            element=ele,
            filepath="soil_mesh.vtk",
            scale=1.0,
        )
        print(mesh_part.tag)
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
        region: Optional[RegionBase] = None,
        *,
        mesh: Optional[pv.DataSet] = None,
        filepath: Optional[str] = None,
        scale: Optional[float] = None,
        rotate_x: Optional[float] = None,
        rotate_y: Optional[float] = None,
        rotate_z: Optional[float] = None,
        translate_x: float = 0.0,
        translate_y: float = 0.0,
        translate_z: float = 0.0,
    ) -> None:
        """Create a custom external mesh part.

        Args:
            user_name: Unique user-defined name for this mesh part.
            element: Associated Element template used for discretization.
            region: Physical Region where this mesh part is added.
            mesh: Optional pre-existing PyVista DataSet object.
            filepath: Optional path to a mesh file on disk (e.g. VTK, VTU, OBJ).
            scale: Optional scale factor greater than 0 applied to the mesh coordinates.
            rotate_x: Optional rotation angle in degrees around the X-axis.
            rotate_y: Optional rotation angle in degrees around the Y-axis.
            rotate_z: Optional rotation angle in degrees around the Z-axis.
            translate_x: Translation offset along the X-axis.
            translate_y: Translation offset along the Y-axis.
            translate_z: Translation offset along the Z-axis.

        Raises:
            ValueError: If both mesh and filepath are provided, if neither is provided,
                or if scale is less than or equal to 0.
            TypeError: If mesh is not a PyVista mesh or filepath is not a string.
            FileNotFoundError: If filepath is provided but the file does not exist.
        """
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
        """Apply specified geometric transformations and cast to an UnstructuredGrid.

        Returns:
            pv.UnstructuredGrid: The fully transformed PyVista UnstructuredGrid.

        Raises:
            ValueError: If casting the transformed mesh to an unstructured grid fails.
        """
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
        """Check if the given element type is compatible with this mesh category.

        Args:
            element: Type name of the element.

        Returns:
            bool: True if compatible, False otherwise.
        """
        return element in cls._compatible_elements


class CompositeMesh(MeshPart):
    """PyVista-based composite structural mesh part wrapping custom node/element collections.

    This class wraps an arbitrary PyVista UnstructuredGrid containing custom element,
    node, material, or section tag metadata. It bypasses regular parametric mesh generation
    and participates directly in model assembly.

    Note:
        - Bypasses standard material assignment methods since material details are typically already baked into the composite grid metadata.

    Example:
        ```python
        import pyvista as pv
        from femora.core.model import Model

        model = Model()
        # Create an arbitrary unstructured grid
        grid = pv.UnstructuredGrid()
        # Create composite mesh part
        composite = model.meshpart.general.composite(
            user_name="structural_shell",
            mesh=grid,
            ndof=6,
        )
        print(composite.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "generate_mesh"],
    }

    _compatible_elements = ["variable"]

    def __init__(
        self,
        user_name: str,
        mesh: pv.UnstructuredGrid,
        region: Optional[RegionBase] = None,
        *,
        ndof: int = 6,
        element_tag: int = 0,
        material_tag: int = 0,
        section_tag: int = 0,
    ) -> None:
        """Create a composite structural mesh part.

        Args:
            user_name: Unique user-defined name for this mesh part.
            mesh: Custom PyVista UnstructuredGrid representing the mesh structure.
            region: Physical Region where this mesh part is added.
            ndof: Number of degrees of freedom per node.
            element_tag: Default fallback OpenSees element tag.
            material_tag: Default fallback OpenSees material tag.
            section_tag: Default fallback OpenSees section tag.

        Raises:
            TypeError: If mesh is not a PyVista UnstructuredGrid.
        """
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
        """Return the wrapped PyVista mesh directly.

        Returns:
            pv.UnstructuredGrid: The wrapped unstructured grid.
        """
        return self.mesh

    def assign_material(self, material: Material) -> None:
        """Bypass standard material assignment as composite meshes use custom internal metadata.

        Args:
            material: The material to bypass.
        """
        pass

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        """Check if the given element type is compatible with this mesh category.

        Args:
            element: Type name of the element.

        Returns:
            bool: Always returns True for composite meshes.
        """
        return True
