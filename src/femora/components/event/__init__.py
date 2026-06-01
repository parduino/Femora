"""---
icon: material/flash-outline
---

Event package for Femora.

This package contains the event system mixins and event-bus components that manage the 
simulation lifecycle and coordinate mesh generation, constraints, and repartitioning 
updates across different model components.

Normal runtime usage should go through `Model` event subscriptions under the 
`model.events` namespace.
"""

from .mixins import (
    GeneratesConstraintsMixin,
    GeneratesMeshMixin,
    GeneratesNodesMixin,
    HandlesDecompositionMixin,
)

__all__ = [
    "GeneratesConstraintsMixin",
    "GeneratesMeshMixin",
    "GeneratesNodesMixin",
    "HandlesDecompositionMixin",
]
