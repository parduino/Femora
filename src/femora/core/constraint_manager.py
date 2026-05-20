from __future__ import annotations

from femora.core.mp_constraint_manager import MPConstraintManager
from femora.core.sp_constraint_manager import SpConstraintManager


class ConstraintManager:
    """MeshMaker-owned manager providing MP/SP constraint namespaces."""

    def __init__(self, mesh_maker):
        from femora.components.MeshMaker import MeshMaker as MeshMakerClass

        if not isinstance(mesh_maker, MeshMakerClass):
            raise TypeError("mesh_maker must be a MeshMaker instance")
        existing_manager = getattr(mesh_maker, "constraint", None)
        if isinstance(existing_manager, ConstraintManager):
            raise ValueError("mesh_maker already owns a constraint manager")
        self._mesh_maker = mesh_maker
        mesh_maker.constraint = self
        self.mp = MPConstraintManager(self)
        self.sp = SpConstraintManager(self)

    def clear(self) -> None:
        self.mp.clear()
        self.sp.clear()

    def set_tag_start(self, start_tag: int) -> None:
        self.mp.set_tag_start(start_tag)
        self.sp.set_tag_start(start_tag)


__all__ = ["ConstraintManager"]
