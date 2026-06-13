# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from femora.components.analysis.convergence_tests import (
    EnergyIncrTest,
    FixedNumIterTest,
    NormDispAndUnbalanceTest,
    NormDispIncrTest,
    NormDispOrUnbalanceTest,
    NormUnbalanceTest,
    RelativeEnergyIncrTest,
    RelativeNormDispIncrTest,
    RelativeNormUnbalanceTest,
    RelativeTotalNormDispIncrTest,
)
from femora.core.analysis.test import Test
from femora.core.tagged_component_manager import TaggedComponentManager


class TestManager(TaggedComponentManager[Test]):
    """Manager for convergence tests on the Analysis model."""

    def __init__(self, analysis_manager) -> None:
        """Initialize the TestManager.

        Args:
            analysis_manager: The parent AnalysisManager instance.
        """
        super().__init__(analysis_manager, Test, "_tests")

    def normunbalance(self, **kwargs) -> Test:
        """Add a NormUnbalanceTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to NormUnbalanceTest.

        Returns:
            The convergence test instance.
        """
        return self.add(NormUnbalanceTest(**kwargs))

    def normdispincr(self, **kwargs) -> Test:
        """Add a NormDispIncrTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to NormDispIncrTest.

        Returns:
            The convergence test instance.
        """
        return self.add(NormDispIncrTest(**kwargs))

    def energyincr(self, **kwargs) -> Test:
        """Add an EnergyIncrTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to EnergyIncrTest.

        Returns:
            The convergence test instance.
        """
        return self.add(EnergyIncrTest(**kwargs))

    def relativenormunbalance(self, **kwargs) -> Test:
        """Add a RelativeNormUnbalanceTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to RelativeNormUnbalanceTest.

        Returns:
            The convergence test instance.
        """
        return self.add(RelativeNormUnbalanceTest(**kwargs))

    def relativenormdispincr(self, **kwargs) -> Test:
        """Add a RelativeNormDispIncrTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to RelativeNormDispIncrTest.

        Returns:
            The convergence test instance.
        """
        return self.add(RelativeNormDispIncrTest(**kwargs))

    def relativetotalnormdispincr(self, **kwargs) -> Test:
        """Add a RelativeTotalNormDispIncrTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to RelativeTotalNormDispIncrTest.

        Returns:
            The convergence test instance.
        """
        return self.add(RelativeTotalNormDispIncrTest(**kwargs))

    def relativeenergyincr(self, **kwargs) -> Test:
        """Add a RelativeEnergyIncrTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to RelativeEnergyIncrTest.

        Returns:
            The convergence test instance.
        """
        return self.add(RelativeEnergyIncrTest(**kwargs))

    def fixednumiter(self, **kwargs) -> Test:
        """Add a FixedNumIterTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to FixedNumIterTest.

        Returns:
            The convergence test instance.
        """
        return self.add(FixedNumIterTest(**kwargs))

    def normdispandunbalance(self, **kwargs) -> Test:
        """Add a NormDispAndUnbalanceTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to NormDispAndUnbalanceTest.

        Returns:
            The convergence test instance.
        """
        return self.add(NormDispAndUnbalanceTest(**kwargs))

    def normdisporunbalance(self, **kwargs) -> Test:
        """Add a NormDispOrUnbalanceTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to NormDispOrUnbalanceTest.

        Returns:
            The convergence test instance.
        """
        return self.add(NormDispOrUnbalanceTest(**kwargs))


__all__ = ["TestManager"]
