from femora.core.event_bus import EventBus, FemoraEvent, ModelEventBus


def test_components_event_bus_shim_reexports_core():
    from femora.components.event.event_bus import (
        EventBus as LegacyEventBus,
        FemoraEvent as LegacyFemoraEvent,
        ModelEventBus as LegacyModelEventBus,
    )

    assert LegacyEventBus is EventBus
    assert LegacyFemoraEvent is FemoraEvent
    assert LegacyModelEventBus is ModelEventBus


def test_model_event_bus_instances_do_not_share_subscribers():
    bus_a = ModelEventBus()
    bus_b = ModelEventBus()
    calls = []

    def on_pre_assemble(**kwargs):
        calls.append("called")

    bus_a.subscribe(FemoraEvent.PRE_ASSEMBLE, on_pre_assemble)

    bus_b.emit(FemoraEvent.PRE_ASSEMBLE)
    assert calls == []

    bus_a.emit(FemoraEvent.PRE_ASSEMBLE)
    assert calls == ["called"]


def test_model_event_bus_does_not_forward_to_global_event_bus():
    EventBus._subscribers.clear()
    global_calls = []

    def global_handler(**kwargs):
        global_calls.append(kwargs.get("marker"))

    EventBus.subscribe(FemoraEvent.PRE_ASSEMBLE, global_handler)

    model_bus = ModelEventBus()
    model_bus.emit(FemoraEvent.PRE_ASSEMBLE, marker="local-only")

    assert global_calls == []


def test_model_event_bus_emits_to_local_subscribers_only():
    EventBus._subscribers.clear()
    local_calls = []

    def local_handler(**kwargs):
        local_calls.append(kwargs.get("assembled_mesh"))

    model_bus = ModelEventBus()
    model_bus.subscribe(FemoraEvent.POST_ASSEMBLE, local_handler)
    model_bus.emit(FemoraEvent.POST_ASSEMBLE, assembled_mesh="mesh")

    assert local_calls == ["mesh"]

