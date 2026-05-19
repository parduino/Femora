from __future__ import annotations


class SpecialElementManager:
    """Bound factory namespace for special-purpose element creation."""

    def __init__(self, manager):
        self._manager = manager

    def ghost_node(self, ndof: int, **kwargs):
        from femora.components.element.ghost_node import GhostNodeElement

        return self._manager.add(GhostNodeElement(ndof, **kwargs))

    def asd_embedded_node(self, ndof: int, **kwargs):
        from femora.components.element.asd_embedded_node import ASDEmbeddedNodeElement3D

        return self._manager.add(ASDEmbeddedNodeElement3D(ndof, **kwargs))

    def zero_length_contact(self, ndof: int, Kn: float, Kt: float, mu: float, **kwargs):
        from femora.components.element.zero_length_contact import ZeroLengthContactASDimplex

        return self._manager.add(
            ZeroLengthContactASDimplex(
                ndof=ndof,
                Kn=Kn,
                Kt=Kt,
                mu=mu,
                **kwargs,
            )
        )


__all__ = ["SpecialElementManager"]
