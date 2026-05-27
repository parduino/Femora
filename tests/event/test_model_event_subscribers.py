import numpy as np

from femora.core.model import Model
from femora.core.event_bus import EventBus, FemoraEvent


def test_mass_manager_subscribes_to_model_event_bus():
    mesh_maker = Model()
    mesh_maker.clear_model()
    EventBus._subscribers.clear()

    mass = mesh_maker.mass
    assert mass._handle_pre_assemble in mesh_maker.events._subscribers[FemoraEvent.PRE_ASSEMBLE]
    assert mass._handle_pre_assemble not in EventBus._subscribers.get(
        FemoraEvent.PRE_ASSEMBLE, []
    )


def test_mask_manager_subscribes_to_model_event_bus():
    mesh_maker = Model()
    mesh_maker.clear_model()
    EventBus._subscribers.clear()

    assert mesh_maker.mask._handle_post_assemble in mesh_maker.events._subscribers[
        FemoraEvent.POST_ASSEMBLE
    ]
    assert mesh_maker.mask._handle_post_assemble not in EventBus._subscribers.get(
        FemoraEvent.POST_ASSEMBLE, []
    )


def test_mass_manager_clears_cache_on_model_pre_assemble():
    mesh_maker = Model()
    mesh_maker.clear_model()

    mass = mesh_maker.mass
    mass._region_point_cache[1] = np.array([0])
    mesh_maker.events.emit(FemoraEvent.PRE_ASSEMBLE)

    assert mass._region_point_cache == {}


def test_clear_model_reregisters_mass_and_mask_subscribers():
    mesh_maker = Model()
    mesh_maker.clear_model()
    EventBus._subscribers.clear()

    mesh_maker.mass._region_point_cache[1] = np.array([0])
    mesh_maker.clear_model()

    assert mesh_maker.mass._handle_pre_assemble in mesh_maker.events._subscribers[
        FemoraEvent.PRE_ASSEMBLE
    ]
    assert mesh_maker.mask._handle_post_assemble in mesh_maker.events._subscribers[
        FemoraEvent.POST_ASSEMBLE
    ]
    assert mesh_maker.mass._region_point_cache == {}
