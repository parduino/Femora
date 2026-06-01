"""---
icon: material/trending-down
---

Damping component package for Femora.

This package contains runtime damping model component classes that are registered
through Femora's damping managers to represent dynamic energy dissipation behavior
in OpenSees.

Normal runtime usage should go through `Model` manager entry points under the
`model.damping` namespace:
- `model.damping.rayleigh(...)` for classic mass- and stiffness-proportional Rayleigh damping
- `model.damping.modal(...)` for mode-specific damping ratios
- `model.damping.frequency_rayleigh(...)` for frequency-based Rayleigh damping parameter generation
- `model.damping.uniform(...)` for uniform damping across a frequency range
- `model.damping.secant_stiffness_proportional(...)` for secant stiffness-proportional damping
"""

from femora.core.damping_base import Damping
from femora.core.damping_manager import DampingManager
from femora.components.damping.dampings import (
    FrequencyRayleighDamping,
    ModalDamping,
    RayleighDamping,
    SecantStiffnessProportional,
    UniformDamping,
)

__all__ = [
    "Damping",
    "DampingManager",
    "RayleighDamping",
    "ModalDamping",
    "FrequencyRayleighDamping",
    "UniformDamping",
    "SecantStiffnessProportional",
]
