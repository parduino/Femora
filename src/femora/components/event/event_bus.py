"""Event-bus API for Femora lifecycle coordination.

This page documents the event objects that power Femora's advanced lifecycle
hooks. A [`Model`][femora.core.model.Model] owns a per-model event bus exposed
as `model.events`. Runtime subsystems such as the assembler emit
[`FemoraEvent`][femora.components.event.event_bus.FemoraEvent] values at key
stages, and subscribed callbacks receive payload data describing what just
happened.

This mechanism is mainly useful for advanced extension work. Ordinary modeling
flows usually create components directly through managers and do not need to
subscribe to events.

Under the hood, the flow looks like this:

1. a runtime subsystem reaches a lifecycle stage such as `POST_ASSEMBLE`
2. it emits a `FemoraEvent` through the model-owned bus
3. subscribers receive keyword-argument payload data
4. advanced components inspect the payload and react

Example:
    ```python
    from femora.core.model import Model
    from femora.components.event.event_bus import FemoraEvent

    model = Model()

    def on_post_assemble(**payload):
        assembled_mesh = payload.get("assembled_mesh")
        if assembled_mesh is not None:
            print(f"assembled cells: {assembled_mesh.n_cells}")

    model.events.subscribe(FemoraEvent.POST_ASSEMBLE, on_post_assemble)
    ```

Tip:
    Prefer the model-owned `model.events` bus for new code. The legacy
    [`EventBus`][femora.components.event.event_bus.EventBus] wrapper is kept
    for compatibility with older code paths and tests.
"""

from femora.core.event_bus import EventBus, FemoraEvent, ModelEventBus

__all__ = ["EventBus", "FemoraEvent", "ModelEventBus"]
