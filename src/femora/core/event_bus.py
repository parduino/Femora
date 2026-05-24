from collections import defaultdict
from enum import Enum, auto
from typing import Callable, Dict, List


class FemoraEvent(Enum):
    """Standard signals that core Femora components emit."""

    PRE_ASSEMBLE = auto()
    POST_ASSEMBLE = auto()
    PRE_EXPORT = auto()
    POST_EXPORT = auto()
    RESOLVE_CORE_CONFLICTS = auto()
    EMBEDDED_BEAM_SOLID_TCL = auto()
    INTERFACE_ELEMENTS_TCL = auto()


class ModelEventBus:
    """Per-model pub/sub bus owned by Model."""

    def __init__(self) -> None:
        self._subscribers: Dict[FemoraEvent, List[Callable]] = defaultdict(list)

    def subscribe(self, event: FemoraEvent, callback: Callable) -> None:
        if callback not in self._subscribers[event]:
            self._subscribers[event].append(callback)

    def unsubscribe(self, event: FemoraEvent, callback: Callable) -> None:
        subscribers = self._subscribers[event]
        if callback in subscribers:
            subscribers.remove(callback)

    def emit(self, event: FemoraEvent, **payload) -> None:
        for callback in list(self._subscribers[event]):
            callback(**payload)

    def clear(self) -> None:
        self._subscribers.clear()


class EventBus:
    """Legacy process-global compatibility wrapper using ModelEventBus internally."""

    _bus = ModelEventBus()
    _subscribers = _bus._subscribers

    @classmethod
    def _sync_bus(cls) -> None:
        # Preserve compatibility if tests or old code replace _subscribers directly.
        cls._bus._subscribers = cls._subscribers

    @classmethod
    def subscribe(cls, event: FemoraEvent, callback: Callable) -> None:
        cls._sync_bus()
        cls._bus.subscribe(event, callback)

    @classmethod
    def unsubscribe(cls, event: FemoraEvent, callback: Callable) -> None:
        cls._sync_bus()
        cls._bus.unsubscribe(event, callback)

    @classmethod
    def emit(cls, event: FemoraEvent, **payload) -> None:
        cls._sync_bus()
        cls._bus.emit(event, **payload)
