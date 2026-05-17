"""Specialized section models."""

from femora.core.section_manager import SectionManager
from femora.components.section.special.bidirectional import BidirectionalSection
from femora.components.section.special.isolator2spring import Isolator2SpringSection

SectionManager.register_section_type("Bidirectional", BidirectionalSection)
SectionManager.register_section_type("Isolator2spring", Isolator2SpringSection)

__all__ = ["BidirectionalSection", "Isolator2SpringSection"]
