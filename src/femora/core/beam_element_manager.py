from __future__ import annotations


class BeamElementManager:
    """Bound factory namespace for beam-like element creation."""

    def __init__(self, manager):
        self._manager = manager

    def elastic(self, ndof: int, section, transformation, **kwargs):
        from femora.components.element.elastic_beam_column import ElasticBeamColumnElement

        sec = self._manager._resolve_section(section)
        transf = self._manager._resolve_transformation(transformation)
        return self._manager.add(ElasticBeamColumnElement(ndof, sec, transf, **kwargs))

    def disp(self, ndof: int, section, transformation, **kwargs):
        from femora.components.element.disp_beam_column import DispBeamColumnElement

        sec = self._manager._resolve_section(section)
        transf = self._manager._resolve_transformation(transformation)
        return self._manager.add(DispBeamColumnElement(ndof, sec, transf, **kwargs))

    def force(self, ndof: int, section, transformation, **kwargs):
        from femora.components.element.force_beam_column import ForceBeamColumnElement

        sec = self._manager._resolve_section(section)
        transf = self._manager._resolve_transformation(transformation)
        return self._manager.add(ForceBeamColumnElement(ndof, sec, transf, **kwargs))

    def truss(self, ndof: int, section, rho: float = 0.0, cMass: int = 0, doRayleigh: int = 0, **kwargs):
        from femora.components.element.truss import TrussElement

        sec = self._manager._resolve_section(section)
        return self._manager.add(
            TrussElement(
                ndof,
                section=sec,
                rho=rho,
                cMass=cMass,
                doRayleigh=doRayleigh,
                **kwargs,
            )
        )


__all__ = ["BeamElementManager"]
