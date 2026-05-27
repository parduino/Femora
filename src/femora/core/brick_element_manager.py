from __future__ import annotations


class BrickElementManager:
    """Bound factory namespace for brick-like element creation."""

    def __init__(self, manager):
        self._manager = manager

    def std(self, ndof: int, material, **kwargs):
        from femora.components.element.std_brick import stdBrickElement

        mat = self._manager._resolve_materials(material)
        return self._manager.add(stdBrickElement(ndof, mat, **kwargs))

    def pml3d(self, ndof: int, material, **kwargs):
        from femora.components.element.pml_3d import PML3DElement

        mat = self._manager._resolve_materials(material)
        return self._manager.add(PML3DElement(ndof, mat, **kwargs))

    def ssp(self, ndof: int, material, **kwargs):
        from femora.components.element.ssp_brick import SSPbrickElement

        mat = self._manager._resolve_materials(material)
        return self._manager.add(SSPbrickElement(ndof, mat, **kwargs))


__all__ = ["BrickElementManager"]
