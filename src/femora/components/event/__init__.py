"""---
icon: material/flash-outline
---

Advanced lifecycle event API for Femora.

The `event` package documents the runtime lifecycle hooks used by Femora's
assembler, exporters, and advanced interface-like components. This is not a
normal modeling surface like `material`, `element`, or `pattern`. Most users
building ordinary models do not need to interact with it directly.

You should come to this package when you need to understand or extend *when*
something happens in the model lifecycle rather than *what* object to create.
Typical use cases include:

- subscribing to assembly or export hooks
- building a custom interface that waits for the assembled mesh
- reacting to repartitioning or core updates
- wiring advanced export-time augmentation

In normal usage, a [`Model`][femora.core.model.Model] owns the event bus
through `model.events`. Runtime subsystems emit a [`FemoraEvent`][femora.components.event.event_bus.FemoraEvent],
and subscribed callbacks or model-owned components react to that lifecycle
stage.

Read this package as an advanced companion to the rest of the API reference:

- the guide explains the lifecycle conceptually
- the event bus page explains the actual subscription API
- the mixin pages explain how advanced components participate in those stages

!!! tip "Start with the guide"
    If you are new to Femora events, start with the API reference guide before
    reading the event bus or mixin pages. The guide explains the lifecycle in
    plain language and shows the role these hooks play under the hood.
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
