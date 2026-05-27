from typing import Optional, Tuple

import numpy as np
import pyvista as pv

from femora.core.element_base import Element
from femora.core.meshpart_base import MeshPart
from femora.core.region_base import RegionBase


class CircularOGrid2D(MeshPart):
    """Parametric structured 2D circular mesh part with an O-Grid topology.

    This mesh part discretizes a circular domain into structured quad elements using
    a central square grid block surrounded by four transition block grids (O-Grid topology).
    This provides structured mesh quality without coordinate singularity at the center,
    ideal for modeling circular piles, shaft sections, or circular domain boundaries.

    Note:
        - Exposes a custom node stitching utility (`_merge_nodes`) to merge coincident coordinates across adjacent grid blocks.
        - Requires quad elements (such as `sspquad` or `stdquad`).

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        mat = model.material.nd.elastic_isotropic(user_name="soil", e_mod=30000.0, nu=0.3, rho=2.0)
        ele = model.element.quad.ssp(ndof=2, material=mat)

        # Discretize a 2D circular cross-section of radius 5.0
        circle = model.meshpart.surface.circular_o_grid(
            user_name="circular_pile_sec",
            element=ele,
            R=5.0,
            r0_ratio=0.4,
            nt=12,
            nr=6,
        )
        print(circle.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "generate_mesh"],
    }

    _compatible_elements = [
        "sspquad", "stdquad"
    ]

    def __init__(
        self,
        user_name: str,
        element: Element,
        region: Optional[RegionBase] = None,
        *,
        R: float,
        r0_ratio: float = 0.4,
        nt: int = 24,
        nr: int = 12,
        merge_tolerance: float = 1e-12,
    ) -> None:
        """Create a parametric 2D circular O-Grid mesh part.

        Args:
            user_name: Unique user-defined name for this mesh part.
            element: Associated Element template used for discretization.
            region: Physical Region where this mesh part is added.
            R: Radius of the circular domain (must be greater than 0).
            r0_ratio: Ratio of the inner central square size to the outer radius (must be between 0.1 and 0.9).
            nt: Number of element intervals along each block transition edge.
            nr: Number of radial element intervals in the outer ring block.
            merge_tolerance: Distance tolerance used to stitch adjacent block nodes.

        Raises:
            ValueError: If R <= 0, r0_ratio is outside (0.1, 0.9), nt or nr is less than 1,
                or if the element type is not a compatible quad element.
        """
        super().__init__(
            category='surface mesh',
            mesh_type='Circular O-Grid',
            user_name=user_name,
            element=element,
            region=region,
        )

        self.R = float(R)
        self.r0_ratio = float(r0_ratio)
        self.nt = int(nt)
        self.nr = int(nr)
        self.merge_tolerance = float(merge_tolerance)

        if self.R <= 0:
            raise ValueError("R must be > 0")
        if not (0.1 < self.r0_ratio < 0.9):
            raise ValueError("r0_ratio must be between 0.1 and 0.9")
        if self.nt < 1 or self.nr < 1:
            raise ValueError("nt and nr must be >= 1")

        if not self.is_elemnt_compatible(element.element_type):
            raise ValueError(
                f"Element type '{element.element_type}' is not compatible with Circular O-Grid 2D mesh"
            )
        self.generate_mesh()

    @staticmethod
    def _merge_nodes(nodes: np.ndarray, quads: np.ndarray, tol: float) -> Tuple[np.ndarray, np.ndarray]:
        """Merge coincident nodes across different grid blocks within a tolerance.

        Args:
            nodes: Unmerged node coordinate array of shape (N, 2).
            quads: Element connectivity index array.
            tol: Distance tolerance below which nodes are merged.

        Returns:
            Tuple[np.ndarray, np.ndarray]: Coincident-merged nodes coordinate array and remapped quads index array.
        """
        node_map = {}
        new_nodes = []
        index_map = {}
        for i, (x, y) in enumerate(nodes):
            key = (round(x / tol) * tol, round(y / tol) * tol)
            if key not in node_map:
                node_map[key] = len(new_nodes)
                new_nodes.append([x, y, 0.0])
            index_map[i] = node_map[key]
        merged_nodes = np.array(new_nodes, dtype=float)
        remapped_quads = np.zeros_like(quads)
        for e, q in enumerate(quads):
            remapped_quads[e] = [index_map[idx] for idx in q]
        return merged_nodes, remapped_quads

    def generate_mesh(self) -> pv.UnstructuredGrid:
        """Construct central and ring block coordinates, merge boundary nodes, and compile a PyVista UnstructuredGrid.

        Returns:
            pv.UnstructuredGrid: The generated circular UnstructuredGrid.
        """
        R = self.R
        r0_ratio = self.r0_ratio
        nt = self.nt
        nr = self.nr
        tol = self.merge_tolerance

        r0 = r0_ratio * R
        a = r0 / np.sqrt(2.0)

        xs = np.linspace(-a, a, nt + 1)
        ys = np.linspace(-a, a, nt + 1)
        nodes_c = np.array([[xs[i], ys[j]] for j in range(nt + 1) for i in range(nt + 1)])
        quads_c = []
        for j in range(nt):
            for i in range(nt):
                n0 = j * (nt + 1) + i
                n1 = n0 + 1
                n2 = n0 + (nt + 1) + 1
                n3 = n0 + (nt + 1)
                quads_c.append([n0, n1, n2, n3])
        quads_c = np.array(quads_c)

        def ring_block(x_in, y_in, x_out, y_out):
            nodes = []
            for i in range(nt + 1):
                xin = x_in[i]; yin = y_in[i]
                xout = x_out[i]; yout = y_out[i]
                for j in range(nr + 1):
                    u = j / nr
                    x = (1 - u) * xin + u * xout
                    y = (1 - u) * yin + u * yout
                    nodes.append([x, y])
            nodes = np.array(nodes)
            quads = []
            for i in range(nt):
                for j in range(nr):
                    n0 = i * (nr + 1) + j
                    n1 = (i + 1) * (nr + 1) + j
                    n2 = (i + 1) * (nr + 1) + (j + 1)
                    n3 = i * (nr + 1) + (j + 1)
                    quads.append([n0, n1, n2, n3])
            return nodes, np.array(quads)

        theta_top = np.linspace(3 * np.pi / 4, np.pi / 4, nt + 1)
        x_in = np.linspace(-a, a, nt + 1); y_in = np.full(nt + 1, a)
        x_out = R * np.cos(theta_top); y_out = R * np.sin(theta_top)
        nodes_t, quads_t = ring_block(x_in, y_in, x_out, y_out)

        theta_r = np.linspace(np.pi / 4, -np.pi / 4, nt + 1)
        x_in = np.full(nt + 1, a); y_in = np.linspace(a, -a, nt + 1)
        x_out = R * np.cos(theta_r); y_out = R * np.sin(theta_r)
        nodes_r, quads_r = ring_block(x_in, y_in, x_out, y_out)

        theta_b = np.linspace(-3 * np.pi / 4, -np.pi / 4, nt + 1)
        x_in = np.linspace(-a, a, nt + 1); y_in = np.full(nt + 1, -a)
        x_out = R * np.cos(theta_b); y_out = R * np.sin(theta_b)
        nodes_b, quads_b = ring_block(x_in, y_in, x_out, y_out)

        theta_l = np.linspace(5 * np.pi / 4, 3 * np.pi / 4, nt + 1)
        x_in = np.full(nt + 1, -a); y_in = np.linspace(-a, a, nt + 1)
        x_out = R * np.cos(theta_l); y_out = R * np.sin(theta_l)
        nodes_l, quads_l = ring_block(x_in, y_in, x_out, y_out)

        nodes_all = np.vstack([nodes_c, nodes_t, nodes_r, nodes_b, nodes_l])
        quads_all = []
        offset = 0
        for nodes_block, quads_block in [
            (nodes_c, quads_c), (nodes_t, quads_t), (nodes_r, quads_r), (nodes_b, quads_b), (nodes_l, quads_l)
        ]:
            quads_all.append(quads_block + offset)
            offset += len(nodes_block)
        quads_all = np.vstack(quads_all)

        merged_nodes, merged_quads = self._merge_nodes(nodes_all, quads_all, tol=tol)

        ncells = merged_quads.shape[0]
        cells = np.hstack([np.column_stack([np.full(ncells, 4), merged_quads])]).flatten()
        celltypes = np.full(ncells, 9, dtype=np.uint8)
        self.mesh = pv.UnstructuredGrid(cells, celltypes, merged_nodes)
        return self.mesh

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        """Check if the given element type is compatible with circular O-grid meshes.

        Args:
            element: Type name of the element.

        Returns:
            bool: True if compatible, False otherwise.
        """
        return element in cls._compatible_elements
