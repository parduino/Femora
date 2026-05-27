from __future__ import annotations

from typing import Optional, Sequence

from femora.core.pattern_base import Pattern


class H5DRMPattern(Pattern):
    """OpenSees H5DRM pattern for Domain Reduction Method boundary loading.

    This pattern references an HDF5-based Domain Reduction Method (DRM) dataset and
    configures how dataset coordinates and loads map into the analysis model, including
    optional coordinate transformations and transformed origin offsets.

    Tcl form:
        ``pattern H5DRM <tag> "<filepath>" <factor> <crdScale> <distanceTolerance> <doCoordinateTransformation> <T00> <T01> <T02> <T10> <T11> <T12> <T20> <T21> <T22> <x00> <x01> <x02>``

    Note:
        - The H5DRM pattern is typically used in large-scale wave propagation models to apply boundary excitations generated from external site response simulations.
        - Nodes in the finite element mesh that lie on the DRM boundary are matched with dataset points within the specified `distance_tolerance`.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        pattern = model.pattern.h5drm(
            filepath="drmload.h5drm",
            factor=1.0,
            crd_scale=1.0,
            distance_tolerance=1.0e-6,
            do_coordinate_transformation=1,
            transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
            origin=[0.0, 0.0, 0.0],
        )
        print(pattern.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        filepath: str,
        factor: float,
        crd_scale: float,
        distance_tolerance: float,
        do_coordinate_transformation: int,
        transform_matrix: Optional[Sequence[float]] = None,
        origin: Optional[Sequence[float]] = None,
        **kwargs,
    ):
        """Create an H5DRM pattern with coordinate mapping parameters.

        Args:
            filepath: Path to the H5DRM dataset file.
            factor: Scale factor applied to DRM forces and displacements.
            crd_scale: Coordinate scale factor for the dataset.
            distance_tolerance: Tolerance used to match DRM dataset points to mesh nodes.
            do_coordinate_transformation: Flag (0 or 1) controlling coordinate transformation.
            transform_matrix: Optional 9-value sequence representing a 3x3 transformation matrix.
                If not supplied, T00 through T22 must be present in kwargs.
            origin: Optional 3-value sequence representing the transformed origin coordinate.
                If not supplied, x00 through x02 must be present in kwargs.
            **kwargs: Compatibility support for individual matrix or origin entries.

        Raises:
            ValueError: If do_coordinate_transformation is not 0 or 1, or if
                transform_matrix or origin sequences have invalid lengths.
            KeyError: If required individual matrix/origin keys are missing from kwargs when not using sequences.
        """
        super().__init__("H5DRM")
        self.filepath = str(filepath)
        self.factor = float(factor)
        self.crd_scale = float(crd_scale)
        self.distance_tolerance = float(distance_tolerance)
        self.do_coordinate_transformation = int(do_coordinate_transformation)
        if self.do_coordinate_transformation not in (0, 1):
            raise ValueError("do_coordinate_transformation must be 0 or 1")

        if transform_matrix is None:
            keys = ("T00", "T01", "T02", "T10", "T11", "T12", "T20", "T21", "T22")
            transform_matrix = [kwargs[key] for key in keys]
        self.transform_matrix = [float(value) for value in transform_matrix]
        if len(self.transform_matrix) != 9:
            raise ValueError("transform_matrix must contain 9 values")

        if origin is None:
            keys = ("x00", "x01", "x02")
            origin = [kwargs[key] for key in keys]
        self.origin = [float(value) for value in origin]
        if len(self.origin) != 3:
            raise ValueError("origin must contain 3 values")

    def to_tcl(self) -> str:
        """Render this pattern as an OpenSees Tcl command.

        Returns:
            str: Tcl command string for the H5DRM pattern.

        Raises:
            ValueError: If the pattern has not been assigned a manager tag.
        """
        matrix = " ".join(map(str, self.transform_matrix))
        origin = " ".join(map(str, self.origin))
        return (
            f'pattern H5DRM {self._require_tag()} "{self.filepath}" '
            f"{self.factor} {self.crd_scale} {self.distance_tolerance} "
            f"{self.do_coordinate_transformation} {matrix} {origin}"
        )
