"""Event bus utilities for managing the simulation lifecycle.

This module exposes the event-bus components that manage publish-subscribe signals in 
Femora models. These signals allow loose coupling between different subsystems, such 
as coordinating mesh generation, constraint resolution, and solver-level actions.

Normal usage involves subscribing to lifecycle signals emitted by the `Model`:

Example:
    ```python
    from femora.core.model import Model
    from femora.components.event.event_bus import FemoraEvent

    model = Model()

    def on_post_assemble(**kwargs):
        print("Model assembly complete.")

    model.events.subscribe(FemoraEvent.POST_ASSEMBLE, on_post_assemble)
    ```
"""

from femora.core.event_bus import EventBus, FemoraEvent, ModelEventBus

__all__ = ["EventBus", "FemoraEvent", "ModelEventBus"]
