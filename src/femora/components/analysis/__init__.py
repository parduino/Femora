"""Analysis component package for Femora.

This package contains runtime analysis component classes that combine to form
complete OpenSees structural analyses. It supports static, transient, and variable
time-step transient analyses.

An analysis is composed of six modular components registered through `model.analysis`:
- **Constraint Handlers**: `model.analysis.constraint` (Plain, Transformation, Penalty, Lagrange, Auto)
- **Numberers**: `model.analysis.numberer` (Plain, RCM, AMD, ParallelRCM)
- **Systems**: `model.analysis.system` (FullGeneral, BandGeneral, BandSPD, ProfileSPD, SuperLU, Umfpack, Mumps)
- **Algorithms**: `model.analysis.algorithm` (Newton, ModifiedNewton, KrylovNewton, BFGS, Broyden, Linear)
- **Convergence Tests**: `model.analysis.test` (NormUnbalance, NormDispIncr, EnergyIncr, NormDispAndUnbalance)
- **Integrators**: `model.analysis.integrator` (LoadControl, DisplacementControl, Newmark, HHT, GeneralizedAlpha)

Normal runtime usage should go through direct creation of `Analysis` instances, which are
then added to the model using `model.analysis.add(analysis)`. Alternatively, a default transient
analysis can be created directly using `model.analysis.default_transient(...)`.
"""
