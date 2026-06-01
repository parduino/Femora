from __future__ import annotations

from typing import List

from femora.components.analysis.integrators import (
    ArcLengthIntegrator,
    CentralDifferenceIntegrator,
    DisplacementControlIntegrator,
    ExplicitDifferenceIntegrator,
    GeneralizedAlphaIntegrator,
    HHTIntegrator,
    LoadControlIntegrator,
    MinUnbalDispNormIntegrator,
    NewmarkIntegrator,
    ParallelDisplacementControlIntegrator,
    PFEMIntegrator,
    TRBDF2Integrator,
)
from femora.core.analysis.integrator import Integrator, StaticIntegrator, TransientIntegrator
from femora.core.tagged_component_manager import TaggedComponentManager


class IntegratorManager(TaggedComponentManager[Integrator]):
    """Manager for integrators on the Analysis model."""

    def __init__(self, analysis_manager) -> None:
        """Initialize the IntegratorManager.

        Args:
            analysis_manager: The parent AnalysisManager instance.
        """
        super().__init__(analysis_manager, Integrator, "_integrators")

    def loadcontrol(self, **kwargs) -> Integrator:
        """Add a LoadControlIntegrator static integrator.

        Args:
            **kwargs: Keyword arguments passed to LoadControlIntegrator.

        Returns:
            The static integrator instance.
        """
        return self.add(LoadControlIntegrator(**kwargs))

    def displacementcontrol(self, **kwargs) -> Integrator:
        """Add a DisplacementControlIntegrator static integrator.

        Args:
            **kwargs: Keyword arguments passed to DisplacementControlIntegrator.

        Returns:
            The static integrator instance.
        """
        return self.add(DisplacementControlIntegrator(**kwargs))

    def paralleldisplacementcontrol(self, **kwargs) -> Integrator:
        """Add a ParallelDisplacementControlIntegrator static integrator.

        Args:
            **kwargs: Keyword arguments passed to ParallelDisplacementControlIntegrator.

        Returns:
            The static integrator instance.
        """
        return self.add(ParallelDisplacementControlIntegrator(**kwargs))

    def minunbaldispnorm(self, **kwargs) -> Integrator:
        """Add a MinUnbalDispNormIntegrator static integrator.

        Args:
            **kwargs: Keyword arguments passed to MinUnbalDispNormIntegrator.

        Returns:
            The static integrator instance.
        """
        return self.add(MinUnbalDispNormIntegrator(**kwargs))

    def arclength(self, **kwargs) -> Integrator:
        """Add an ArcLengthIntegrator static integrator.

        Args:
            **kwargs: Keyword arguments passed to ArcLengthIntegrator.

        Returns:
            The static integrator instance.
        """
        return self.add(ArcLengthIntegrator(**kwargs))

    def centraldifference(self, **kwargs) -> Integrator:
        """Add a CentralDifferenceIntegrator transient integrator.

        Args:
            **kwargs: Keyword arguments passed to CentralDifferenceIntegrator.

        Returns:
            The transient integrator instance.
        """
        return self.add(CentralDifferenceIntegrator(**kwargs))

    def newmark(self, **kwargs) -> Integrator:
        """Add a NewmarkIntegrator transient integrator.

        Args:
            **kwargs: Keyword arguments passed to NewmarkIntegrator.

        Returns:
            The transient integrator instance.
        """
        return self.add(NewmarkIntegrator(**kwargs))

    def hht(self, **kwargs) -> Integrator:
        """Add an HHTIntegrator transient integrator.

        Args:
            **kwargs: Keyword arguments passed to HHTIntegrator.

        Returns:
            The transient integrator instance.
        """
        return self.add(HHTIntegrator(**kwargs))

    def generalizedalpha(self, **kwargs) -> Integrator:
        """Add a GeneralizedAlphaIntegrator transient integrator.

        Args:
            **kwargs: Keyword arguments passed to GeneralizedAlphaIntegrator.

        Returns:
            The transient integrator instance.
        """
        return self.add(GeneralizedAlphaIntegrator(**kwargs))

    def trbdf2(self, **kwargs) -> Integrator:
        """Add a TRBDF2Integrator transient integrator.

        Args:
            **kwargs: Keyword arguments passed to TRBDF2Integrator.

        Returns:
            The transient integrator instance.
        """
        return self.add(TRBDF2Integrator(**kwargs))

    def explicitdifference(self, **kwargs) -> Integrator:
        """Add an ExplicitDifferenceIntegrator transient integrator.

        Args:
            **kwargs: Keyword arguments passed to ExplicitDifferenceIntegrator.

        Returns:
            The transient integrator instance.
        """
        return self.add(ExplicitDifferenceIntegrator(**kwargs))

    def pfem(self, **kwargs) -> Integrator:
        """Add a PFEMIntegrator transient integrator.

        Args:
            **kwargs: Keyword arguments passed to PFEMIntegrator.

        Returns:
            The transient integrator instance.
        """
        return self.add(PFEMIntegrator(**kwargs))

    def get_static_types(self) -> List[str]:
        """Get available static integrator types.

        Returns:
            A list of static integrator type names.
        """
        return StaticIntegrator.get_static_types()

    def get_transient_types(self) -> List[str]:
        """Get available transient integrator types.

        Returns:
            A list of transient integrator type names.
        """
        return TransientIntegrator.get_transient_types()


__all__ = ["IntegratorManager"]
