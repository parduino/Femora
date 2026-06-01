from __future__ import annotations

from femora.components.analysis.algorithms import (
    BFGSAlgorithm,
    BroydenAlgorithm,
    ExpressNewtonAlgorithm,
    KrylovNewtonAlgorithm,
    LinearAlgorithm,
    ModifiedNewtonAlgorithm,
    NewtonAlgorithm,
    NewtonLineSearchAlgorithm,
    SecantNewtonAlgorithm,
)
from femora.core.analysis.algorithm import Algorithm
from femora.core.tagged_component_manager import TaggedComponentManager


class AlgorithmManager(TaggedComponentManager[Algorithm]):
    def __init__(self, analysis_manager) -> None:
        super().__init__(analysis_manager, Algorithm, "_algorithms")

    def linear(self, **kwargs) -> Algorithm:
        return self.add(LinearAlgorithm(**kwargs))

    def newton(self, **kwargs) -> Algorithm:
        return self.add(NewtonAlgorithm(**kwargs))

    def modifiednewton(self, **kwargs) -> Algorithm:
        return self.add(ModifiedNewtonAlgorithm(**kwargs))

    def newtonlinesearch(self, **kwargs) -> Algorithm:
        return self.add(NewtonLineSearchAlgorithm(**kwargs))

    def krylovnewton(self, **kwargs) -> Algorithm:
        return self.add(KrylovNewtonAlgorithm(**kwargs))

    def secantnewton(self, **kwargs) -> Algorithm:
        return self.add(SecantNewtonAlgorithm(**kwargs))

    def bfgs(self, **kwargs) -> Algorithm:
        return self.add(BFGSAlgorithm(**kwargs))

    def broyden(self, **kwargs) -> Algorithm:
        return self.add(BroydenAlgorithm(**kwargs))

    def expressnewton(self, **kwargs) -> Algorithm:
        return self.add(ExpressNewtonAlgorithm(**kwargs))


__all__ = ["AlgorithmManager"]
