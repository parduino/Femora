"""---
icon: material/record-rec
---

Recorder component package for Femora.

This package contains runtime recorder component classes that represent OpenSees
``recorder`` commands. Recorders capture and export structural responses (such
as displacements, reactions, or element forces) during dynamic or static analyses.

Normal runtime usage should go through `Model` manager entry points under the
`model.recorder` namespace:
- `model.recorder.node(...)` to record node responses
- `model.recorder.drift(...)` to record inter-story drift ratios
- `model.recorder.vtkhdf(...)` to record dynamic whole-model geometry and results
- `model.recorder.mpco(...)` to record STKO-compatible HDF5 databases
- `model.recorder.beam_force(...)` to record line mesh element forces
"""

from femora.components.recorder import recorders

__all__ = ["recorders"]
