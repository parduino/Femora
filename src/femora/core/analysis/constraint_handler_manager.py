from __future__ import annotations

from femora.components.analysis.constraint_handlers import (
    AutoConstraintHandler,
    LagrangeConstraintHandler,
    PenaltyConstraintHandler,
    PlainConstraintHandler,
    TransformationConstraintHandler,
)
from femora.core.analysis.constraint_handler import ConstraintHandler
from femora.core.tagged_component_manager import TaggedComponentManager


class ConstraintHandlerManager(TaggedComponentManager[ConstraintHandler]):
    def __init__(self, analysis_manager) -> None:
        super().__init__(analysis_manager, ConstraintHandler, "_handlers")

    def plain(self, **kwargs) -> ConstraintHandler:
        return self.add(PlainConstraintHandler(**kwargs))

    def transformation(self, **kwargs) -> ConstraintHandler:
        return self.add(TransformationConstraintHandler(**kwargs))

    def penalty(self, **kwargs) -> ConstraintHandler:
        return self.add(PenaltyConstraintHandler(**kwargs))

    def lagrange(self, **kwargs) -> ConstraintHandler:
        return self.add(LagrangeConstraintHandler(**kwargs))

    def auto(self, **kwargs) -> ConstraintHandler:
        return self.add(AutoConstraintHandler(**kwargs))


__all__ = ["ConstraintHandlerManager"]
