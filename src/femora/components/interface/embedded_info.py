from typing import List, Tuple, Set, FrozenSet, Optional, Union
from dataclasses import dataclass, field
import hashlib


@dataclass(frozen=True)
class EmbeddedInfo:
    """Optimized EmbeddedInfo data structure for fast interface comparisons.
    
    This structure tracks connection mapping between embedded beam elements 
    and surrounding solid elements, deduplicating equivalent layouts and 
    detecting core partition conflicts.
    """
    
    # Store beams as frozenset for immutability and fast equality
    beams: FrozenSet[int]
    core_number: int
    
    # Internal optimized representations
    _beams_solids_canonical: Tuple[Tuple[Tuple[int, ...], Tuple[int, ...]], ...] = field(repr=False)
    _list1_hashes: FrozenSet[str] = field(repr=False)
    _beams_solids_hash: str = field(repr=False)
    _solids_set: FrozenSet[int] = field(repr=False)
    
    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, beams: Union[List[int], Set[int]], core_number: int, 
                 beams_solids: List[Tuple[List[int], List[int]]]):
        """Create an EmbeddedInfo instance.

        Args:
            beams: A set or list of integers representing beam element identifiers.
            core_number: An integer core partition ID.
            beams_solids: List of (list1, list2) mapping tuples, where list1 is
                the beam connectivity list and list2 is the solid element ID list.
        """
        # Convert beams to frozenset
        object.__setattr__(self, 'beams', frozenset(beams))
        object.__setattr__(self, 'core_number', core_number)
        
        # Canonicalize beams_solids: sort each tuple internally, then sort all tuples
        canonical_tuples = []
        list1_hashes = set()
        solids_seen = set()
        
        for list1, list2 in beams_solids:
            # Convert to tuples for immutability
            tuple1 = tuple(sorted(list1))  # Keep original order for list1 (conflict detection)
            tuple2 = tuple(sorted(list2))  # Sort list2 for consistency
            
            # Hash list1 for fast conflict detection
            list1_hash = hashlib.md5(str(tuple1).encode()).hexdigest()
            list1_hashes.add(list1_hash)
            
            canonical_tuples.append((tuple1, tuple2))

            # collect solids for similarity checks based on solid overlap
            for s in tuple2:
                solids_seen.add(s)
        
        # Sort tuples by their string representation for canonical form
        canonical_tuples.sort(key=lambda x: (x[0], x[1]))
        
        # Store canonical representation
        object.__setattr__(self, '_beams_solids_canonical', tuple(canonical_tuples))
        object.__setattr__(self, '_list1_hashes', frozenset(list1_hashes))
        
        # Pre-compute hash for beams_solids
        beams_solids_str = str(self._beams_solids_canonical)
        beams_solids_hash = hashlib.md5(beams_solids_str.encode()).hexdigest()
        object.__setattr__(self, '_beams_solids_hash', beams_solids_hash)

        # Store solids set
        object.__setattr__(self, '_solids_set', frozenset(solids_seen))

    # Expose solids_set read-only
    @property
    def solids_set(self) -> FrozenSet[int]:
        """Get the set of solid elements associated with this interface."""
        return self._solids_set
    
    @property
    def beams_solids(self) -> List[Tuple[List[int], List[int]]]:
        """Get beams_solids in list format for compatibility."""
        return [(list(t1), list(t2)) for t1, t2 in self._beams_solids_canonical]
    
    def __eq__(self, other: object) -> bool:
        """Check if two EmbeddedInfo objects are logically equal in O(1) time."""
        if not isinstance(other, EmbeddedInfo):
            return False
        
        # Fast checks first
        if self.beams != other.beams:
            return False
        if self.core_number != other.core_number:
            return False
        
        # Compare pre-computed hashes
        return self._beams_solids_hash == other._beams_solids_hash
    
    def is_conflict(self, other: 'EmbeddedInfo') -> bool:
        """Check if two objects conflict (have the same beams and overlap on list1 connectivities).

        Args:
            other: The other EmbeddedInfo instance to compare.

        Returns:
            True if there is a mapping conflict, False otherwise.
        """
        if not isinstance(other, EmbeddedInfo):
            return False
        
        # Must have same beams
        if self.beams != other.beams:
            return False
        
        # Check if any list1 hash overlaps
        return bool(self._list1_hashes & other._list1_hashes)
    
    def is_similar(self, other: 'EmbeddedInfo') -> bool:
        """Check if two objects are similar (share identical beams or solids without conflict).

        Args:
            other: The other EmbeddedInfo instance to compare.

        Returns:
            True if similar, False otherwise.
        """
        if not isinstance(other, EmbeddedInfo):
            return False

        # Quick conflict rejection
        if self.is_conflict(other):
            return False

        # Original similarity – same beams
        if self.beams == other.beams:
            return True

        # New similarity – overlapping solids
        return bool(self._solids_set & other._solids_set)
    
    def __hash__(self) -> int:
        """Compute the hash using pre-computed canonical values."""
        return hash((self.beams, self.core_number, self._beams_solids_hash))
    
    def compare(self, other: 'EmbeddedInfo') -> str:
        """Compare with another EmbeddedInfo and return the relationship type.
        
        Args:
            other: The other EmbeddedInfo to compare.

        Returns:
            A string indicating the relationship: "equal", "conflict", 
            "similar", or "unrelated".

        Raises:
            TypeError: If other is not an instance of EmbeddedInfo.
        """
        if not isinstance(other, EmbeddedInfo):
            raise TypeError(f"Cannot compare EmbeddedInfo with {type(other)}")
        
        # Check equality first (most specific)
        if self == other:
            return "equal"
        
        # Check conflict first (only possible with same beams)
        if self.beams == other.beams:
            if self._list1_hashes & other._list1_hashes:
                return "conflict"
            # Equal already handled; so same beams, no conflict
            return "similar"

        # Different beams – decide similarity by solid overlap
        if self._solids_set & other._solids_set:
            return "similar"

        return "unrelated"

    def with_core_number(self, new_core_number: int) -> 'EmbeddedInfo':
        """Return a copy of this EmbeddedInfo with a different core_number.

        Args:
            new_core_number: The core partition number for the copy.

        Returns:
            A new EmbeddedInfo instance with the updated core partition.
        """
        return EmbeddedInfo(
            beams=list(self.beams),
            core_number=new_core_number,
            beams_solids=[(list(t1), list(t2)) for t1, t2 in self._beams_solids_canonical]
        )
    
    def __repr__(self) -> str:
        return f"EmbeddedInfo(beams={sorted(self.beams)}, core_number={self.core_number}, beams_solids={self.beams_solids})"