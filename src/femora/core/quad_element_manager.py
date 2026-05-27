from __future__ import annotations


class QuadElementManager:
    """Bound factory namespace for quadrilateral element creation."""

    def __init__(self, manager):
        self._manager = manager

    def ssp(self, ndof: int, material, **kwargs):
        from femora.components.element.ssp_quad import SSPQuadElement

        mat = self._manager._resolve_materials(material)
        return self._manager.add(SSPQuadElement(ndof, mat, **kwargs))


__all__ = ["QuadElementManager"]
