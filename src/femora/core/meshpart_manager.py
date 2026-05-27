from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Union

from femora.core.element_base import Element
from femora.core.meshpart_base import MeshPart
from femora.core.region_base import RegionBase
from femora.core.tagging import CompactRetagPolicy

if TYPE_CHECKING:
    from femora.core.model import Model


class _MeshPartNamespace:
    def __init__(self, manager: "MeshPartManager") -> None:
        self._manager = manager


class LineMeshNamespace(_MeshPartNamespace):
    def single_line(
        self,
        user_name: str,
        element: Element,
        region: Optional[RegionBase] = None,
        *,
        x0: float = 0.0,
        y0: float = 0.0,
        z0: float = 0.0,
        x1: float = 1.0,
        y1: float = 0.0,
        z1: float = 0.0,
        number_of_lines: int = 1,
        merge_points: bool = True,
    ) -> MeshPart:
        from femora.components.mesh.line_meshparts import SingleLineMesh

        return self._manager.add(
            SingleLineMesh(
                user_name,
                element,
                region,
                x0=x0,
                y0=y0,
                z0=z0,
                x1=x1,
                y1=y1,
                z1=z1,
                number_of_lines=number_of_lines,
                merge_points=merge_points,
            )
        )

    def structured_lines(
        self,
        user_name: str,
        element: Element,
        region: Optional[RegionBase] = None,
        *,
        base_point_x: float = 0.0,
        base_point_y: float = 0.0,
        base_point_z: float = 0.0,
        base_vector_1_x: float = 1.0,
        base_vector_1_y: float = 0.0,
        base_vector_1_z: float = 0.0,
        base_vector_2_x: float = 0.0,
        base_vector_2_y: float = 1.0,
        base_vector_2_z: float = 0.0,
        normal_x: float = 0.0,
        normal_y: float = 0.0,
        normal_z: float = 1.0,
        grid_size_1: int = 10,
        grid_size_2: int = 10,
        spacing_1: float = 1.0,
        spacing_2: float = 1.0,
        length: float = 1.0,
        offset_1: float = 0.0,
        offset_2: float = 0.0,
        number_of_lines: int = 1,
        merge_points: bool = True,
    ) -> MeshPart:
        from femora.components.mesh.line_meshparts import StructuredLineMesh

        return self._manager.add(
            StructuredLineMesh(
                user_name,
                element,
                region,
                base_point_x=base_point_x,
                base_point_y=base_point_y,
                base_point_z=base_point_z,
                base_vector_1_x=base_vector_1_x,
                base_vector_1_y=base_vector_1_y,
                base_vector_1_z=base_vector_1_z,
                base_vector_2_x=base_vector_2_x,
                base_vector_2_y=base_vector_2_y,
                base_vector_2_z=base_vector_2_z,
                normal_x=normal_x,
                normal_y=normal_y,
                normal_z=normal_z,
                grid_size_1=grid_size_1,
                grid_size_2=grid_size_2,
                spacing_1=spacing_1,
                spacing_2=spacing_2,
                length=length,
                offset_1=offset_1,
                offset_2=offset_2,
                number_of_lines=number_of_lines,
                merge_points=merge_points,
            )
        )


class VolumeMeshNamespace(_MeshPartNamespace):
    def uniform_rectangular_grid(
        self,
        user_name: str,
        element: Element,
        region: Optional[RegionBase] = None,
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
    ) -> MeshPart:
        from femora.components.mesh.volume_meshparts import StructuredRectangular3D

        return self._manager.add(
            StructuredRectangular3D(
                user_name,
                element,
                region,
                x_min=x_min,
                x_max=x_max,
                y_min=y_min,
                y_max=y_max,
                z_min=z_min,
                z_max=z_max,
                nx=nx,
                ny=ny,
                nz=nz,
            )
        )

    def custom_rectangular_grid(
        self,
        user_name: str,
        element: Element,
        region: Optional[RegionBase] = None,
        *,
        x_coords: str,
        y_coords: str,
        z_coords: str,
    ) -> MeshPart:
        from femora.components.mesh.volume_meshparts import CustomRectangularGrid3D

        return self._manager.add(
            CustomRectangularGrid3D(
                user_name,
                element,
                region,
                x_coords=x_coords,
                y_coords=y_coords,
                z_coords=z_coords,
            )
        )

    def geometric_rectangular_grid(
        self,
        user_name: str,
        element: Element,
        region: Optional[RegionBase] = None,
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
    ) -> MeshPart:
        from femora.components.mesh.volume_meshparts import GeometricStructuredRectangular3D

        return self._manager.add(
            GeometricStructuredRectangular3D(
                user_name,
                element,
                region,
                x_min=x_min,
                x_max=x_max,
                y_min=y_min,
                y_max=y_max,
                z_min=z_min,
                z_max=z_max,
                nx=nx,
                ny=ny,
                nz=nz,
                x_ratio=x_ratio,
                y_ratio=y_ratio,
                z_ratio=z_ratio,
            )
        )


class SurfaceMeshNamespace(_MeshPartNamespace):
    def circular_o_grid(
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
    ) -> MeshPart:
        from femora.components.mesh.surface_meshparts import CircularOGrid2D

        return self._manager.add(
            CircularOGrid2D(
                user_name,
                element,
                region,
                R=R,
                r0_ratio=r0_ratio,
                nt=nt,
                nr=nr,
                merge_tolerance=merge_tolerance,
            )
        )


class GeneralMeshNamespace(_MeshPartNamespace):
    def external_mesh(
        self,
        user_name: str,
        element: Element,
        region: Optional[RegionBase] = None,
        *,
        mesh=None,
        filepath: str | None = None,
        scale: float | None = None,
        rotate_x: float | None = None,
        rotate_y: float | None = None,
        rotate_z: float | None = None,
        translate_x: float = 0.0,
        translate_y: float = 0.0,
        translate_z: float = 0.0,
    ) -> MeshPart:
        from femora.components.mesh.general_meshparts import ExternalMesh

        return self._manager.add(
            ExternalMesh(
                user_name,
                element,
                region,
                mesh=mesh,
                filepath=filepath,
                scale=scale,
                rotate_x=rotate_x,
                rotate_y=rotate_y,
                rotate_z=rotate_z,
                translate_x=translate_x,
                translate_y=translate_y,
                translate_z=translate_z,
            )
        )

    def composite(
        self,
        user_name: str,
        mesh,
        region: Optional[RegionBase] = None,
        *,
        ndof: int = 6,
        element_tag: int = 0,
        material_tag: int = 0,
        section_tag: int = 0,
    ) -> MeshPart:
        from femora.components.mesh.general_meshparts import CompositeMesh

        return self._manager.add(
            CompositeMesh(
                user_name,
                mesh,
                region,
                ndof=ndof,
                element_tag=element_tag,
                material_tag=material_tag,
                section_tag=section_tag,
            )
        )


class MeshPartManager:
    """Manager-owned lifecycle and tagging for mesh parts on one Model."""

    def __init__(self, mesh_maker: Model):
        from femora.core.model import Model as ModelClass

        if not isinstance(mesh_maker, ModelClass):
            raise TypeError("mesh_maker must be a Model instance")
        existing = getattr(mesh_maker, "meshpart", None)
        if isinstance(existing, MeshPartManager):
            raise ValueError("mesh_maker already owns a meshpart manager")

        self._mesh_maker = mesh_maker
        mesh_maker.meshpart = self
        self._meshparts: Dict[str, MeshPart] = {}
        self._start_tag = 1
        self._tagging = CompactRetagPolicy[MeshPart]()
        self.line = LineMeshNamespace(self)
        self.volume = VolumeMeshNamespace(self)
        self.surface = SurfaceMeshNamespace(self)
        self.general = GeneralMeshNamespace(self)

    def add(self, meshpart: MeshPart) -> MeshPart:
        if not isinstance(meshpart, MeshPart):
            raise TypeError("meshpart must be a MeshPart instance")
        if meshpart.user_name in self._meshparts and self._meshparts[meshpart.user_name] is not meshpart:
            raise ValueError(f"Mesh part name '{meshpart.user_name}' is already in use")
        if meshpart.region is None:
            meshpart.region = self._mesh_maker.region.global_region
        if meshpart._owner is None:
            meshpart._owner = self
        elif meshpart._owner is not self:
            raise ValueError("meshpart already belongs to another manager")
        by_tag = {p.tag: p for p in self._meshparts.values() if p.tag is not None}
        try:
            meshpart.tag = self._tagging.assign_tag(by_tag, meshpart, self._start_tag)
        except ValueError as exc:
            raise ValueError(f"MeshPart tag {meshpart.tag} already exists") from exc
        self._meshparts[meshpart.user_name] = meshpart
        return meshpart

    def get(self, user_name: str) -> Optional[MeshPart]:
        return self._meshparts.get(user_name)

    def get_by_tag(self, tag: int) -> Optional[MeshPart]:
        for part in self._meshparts.values():
            if part.tag == int(tag):
                return part
        return None

    def resolve(self, item: Union[str, int, MeshPart]) -> Optional[MeshPart]:
        if isinstance(item, MeshPart):
            return item
        if isinstance(item, str):
            return self.get(item)
        if isinstance(item, int):
            return self.get_by_tag(item)
        return None

    def get_all(self) -> Dict[str, MeshPart]:
        return dict(self._meshparts)

    def get_by_category(self, category: str) -> Dict[str, MeshPart]:
        key = category.lower()
        return {
            name: part
            for name, part in self._meshparts.items()
            if part.category.lower() == key
        }

    def remove(self, user_name: str) -> None:
        part = self._meshparts.pop(user_name, None)
        if part is not None:
            part.tag = None
            part._owner = None
            self._reassign_tags()

    def clear(self) -> None:
        for part in list(self._meshparts.values()):
            part.tag = None
            part._owner = None
        self._meshparts.clear()

    def set_tag_start(self, start_tag: int) -> None:
        self._start_tag = self._tagging.validate_start_tag(start_tag)
        self._reassign_tags()

    def _reassign_tags(self) -> None:
        by_tag = {p.tag: p for p in self._meshparts.values() if p.tag is not None}
        self._tagging.reassign_tags(by_tag, self._start_tag)


__all__ = ["MeshPartManager"]
