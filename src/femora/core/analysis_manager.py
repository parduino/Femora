from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Union

from femora.components.analysis.algorithms import Algorithm, AlgorithmManager
from femora.components.analysis.analysis import Analysis
from femora.components.analysis.constraint_handlers import ConstraintHandler, ConstraintHandlerManager
from femora.components.analysis.integrators import Integrator, IntegratorManager, StaticIntegrator, TransientIntegrator
from femora.components.analysis.numberers import Numberer
from femora.components.analysis.systems import System, SystemManager
from femora.components.analysis.convergenceTests import Test, TestManager
from femora.core.numberer_manager import NumbererManager
from femora.core.tagging import CompactRetagPolicy

if TYPE_CHECKING:
    from femora.components.MeshMaker import MeshMaker


class AnalysisManager:
    """Manager-owned analysis stack for one MeshMaker model."""

    def __init__(self, mesh_maker: MeshMaker):
        from femora.components.MeshMaker import MeshMaker as MeshMakerClass

        if not isinstance(mesh_maker, MeshMakerClass):
            raise TypeError("mesh_maker must be a MeshMaker instance")
        existing_manager = getattr(mesh_maker, "analysis", None)
        if isinstance(existing_manager, AnalysisManager):
            raise ValueError("mesh_maker already owns an analysis manager")

        self._mesh_maker = mesh_maker
        mesh_maker.analysis = self
        self._analyses: Dict[int, Analysis] = {}
        self._names: Dict[str, Analysis] = {}
        self._start_tag = 1
        self._tagging = CompactRetagPolicy[Analysis]()

        self.test = TestManager(self)
        self.constraint = ConstraintHandlerManager(self)
        self.numberer = NumbererManager(self)
        self.system = SystemManager(self)
        self.algorithm = AlgorithmManager(self)
        self.integrator = IntegratorManager(self)

    def add(self, analysis: Analysis) -> Analysis:
        if not isinstance(analysis, Analysis):
            raise TypeError("analysis must be an Analysis instance")
        if analysis.name in self._names and self._names[analysis.name] is not analysis:
            raise ValueError(f"Analysis name '{analysis.name}' is already in use")
        if analysis._owner is None:
            analysis._owner = self
        elif analysis._owner is not self:
            raise ValueError("analysis already belongs to another manager")
        try:
            analysis.tag = self._tagging.assign_tag(self._analyses, analysis, self._start_tag)
        except ValueError as exc:
            raise ValueError(f"Analysis tag {analysis.tag} already exists") from exc
        self._analyses[analysis.tag] = analysis
        self._names[analysis.name] = analysis
        return analysis

    def default_transient(
        self,
        username: str,
        dt: float,
        num_steps: int | None = None,
        final_time: float | None = None,
        options: dict | None = None,
    ) -> Analysis:
        if (num_steps is None and final_time is None) or (
            num_steps is not None and final_time is not None
        ):
            raise ValueError("Exactly one of num_steps or final_time must be provided")

        options = options or {}
        analysis_name = f"defaultTransient_{username}"
        numberer = options.get("numberer", self.numberer.parallelrcm())
        integrator = options.get(
            "integrator", self.integrator.newmark(gamma=0.5, beta=0.25)
        )
        system = options.get("system", self.system.mumps(icntl14=400, icntl7=7))
        test = options.get(
            "test", self.test.energyincr(tol=1e-3, max_iter=20, print_flag=2)
        )
        algorithm = options.get(
            "algorithm", self.algorithm.modifiednewton(factor_once=True)
        )
        constraint_handler = options.get(
            "constraint_handler", self.constraint.transformation()
        )
        return self.add(
            Analysis(
                analysis_name,
                "Transient",
                constraint_handler,
                numberer,
                system,
                algorithm,
                test,
                integrator,
                num_steps=num_steps,
                final_time=final_time,
                dt=dt,
            )
        )

    def get(self, identifier: Union[int, str, Analysis]) -> Analysis:
        if isinstance(identifier, int):
            analysis = self._analyses.get(identifier)
            if analysis is None:
                raise KeyError(f"No analysis found with tag {identifier}")
            return analysis
        if isinstance(identifier, str):
            analysis = self._names.get(identifier)
            if analysis is None:
                for item in self._analyses.values():
                    if item.name.lower() == identifier.lower():
                        return item
                raise KeyError(f"No analysis found with name '{identifier}'")
            return analysis
        if isinstance(identifier, Analysis):
            return identifier
        raise TypeError(
            f"Identifier must be an int (tag), str (name), or Analysis instance, not {type(identifier)}"
        )

    def get_all(self) -> Dict[int, Analysis]:
        return dict(self._analyses)

    def remove(self, identifier: Union[int, str, Analysis]) -> None:
        analysis = self.get(identifier)
        self._analyses.pop(analysis.tag, None)
        self._names.pop(analysis.name, None)
        analysis.tag = None
        analysis._owner = None
        self._reassign_tags()

    def clear(self) -> None:
        for analysis in list(self._analyses.values()):
            analysis.tag = None
            analysis._owner = None
        self._analyses.clear()
        self._names.clear()
        self.test.clear()
        self.constraint.clear()
        self.numberer.clear()
        self.system.clear()
        self.algorithm.clear()
        self.integrator.clear()

    def set_tag_start(self, start_tag: int) -> None:
        self._start_tag = self._tagging.validate_start_tag(start_tag)
        self._reassign_tags()

    def update_constraint_handler(
        self, identifier: Union[int, str, Analysis], constraint_handler: ConstraintHandler
    ) -> None:
        self.get(identifier).constraint_handler = constraint_handler

    def update_numberer(self, identifier: Union[int, str, Analysis], numberer: Numberer) -> None:
        self.get(identifier).numberer = numberer

    def update_system(self, identifier: Union[int, str, Analysis], system: System) -> None:
        self.get(identifier).system = system

    def update_algorithm(self, identifier: Union[int, str, Analysis], algorithm: Algorithm) -> None:
        self.get(identifier).algorithm = algorithm

    def update_test(self, identifier: Union[int, str, Analysis], test: Test) -> None:
        self.get(identifier).test = test

    def update_integrator(self, identifier: Union[int, str, Analysis], integrator: Integrator) -> None:
        analysis = self.get(identifier)
        if analysis.analysis_type == "Static" and not isinstance(integrator, StaticIntegrator):
            raise ValueError(
                f"Static analysis requires a static integrator. {integrator.integrator_type} is not compatible."
            )
        if analysis.analysis_type in ["Transient", "VariableTransient"] and not isinstance(
            integrator, TransientIntegrator
        ):
            raise ValueError(
                f"Transient analysis requires a transient integrator. {integrator.integrator_type} is not compatible."
            )
        analysis.integrator = integrator

    def _reassign_tags(self) -> None:
        self._tagging.reassign_tags(self._analyses, self._start_tag)
        self._names = {analysis.name: analysis for analysis in self._analyses.values()}


__all__ = ["AnalysisManager"]
