from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Generic, TypeVar


class TaggedObject(ABC):
    """Minimal protocol-like base for manager-owned tagged objects."""

    tag: int | None


TTagged = TypeVar("TTagged", bound=TaggedObject)


class TaggingPolicy(ABC, Generic[TTagged]):
    """Strategy object for manager-local tag assignment and retagging."""

    @staticmethod
    def validate_start_tag(start_tag: int) -> int:
        """Normalize and validate the configured first tag."""
        start_tag = int(start_tag)
        if start_tag < 1:
            raise ValueError("start_tag must be a positive integer")
        return start_tag

    @abstractmethod
    def assign_tag(self, store: Dict[int, TTagged], obj: TTagged, start_tag: int) -> int:
        """Return the tag that should be used when ``obj`` is added."""
        raise NotImplementedError

    @abstractmethod
    def reassign_tags(self, store: Dict[int, TTagged], start_tag: int) -> None:
        """Retag all objects in ``store`` in place."""
        raise NotImplementedError


class CompactRetagPolicy(TaggingPolicy[TTagged]):
    """Assign the next available tag and compact after removals."""

    def assign_tag(self, store: Dict[int, TTagged], obj: TTagged, start_tag: int) -> int:
        if obj.tag is None:
            return self.next_available_tag(store, start_tag)
        if obj.tag in store and store[obj.tag] is not obj:
            raise ValueError(f"Tag {obj.tag} already exists")
        return obj.tag

    def reassign_tags(self, store: Dict[int, TTagged], start_tag: int) -> None:
        items = sorted(
            store.values(),
            key=lambda item: item.tag if item.tag is not None else 0,
        )
        store.clear()
        for offset, obj in enumerate(items):
            obj.tag = start_tag + offset
            store[obj.tag] = obj

    @staticmethod
    def next_available_tag(store: Dict[int, TTagged], start_tag: int) -> int:
        """Return the first unused tag at or above ``start_tag``."""
        tag = start_tag
        while tag in store:
            tag += 1
        return tag


__all__ = [
    "TaggingPolicy",
    "CompactRetagPolicy",
    "TaggedObject",
]
