"""Section types composed from other sections or materials."""

from femora.core.section_manager import SectionManager
from femora.components.section.composite.aggregator import AggregatorSection
from femora.components.section.composite.parallel import ParallelSection

SectionManager.register_section_type("Aggregator", AggregatorSection)
SectionManager.register_section_type("Parallel", ParallelSection)

__all__ = ["AggregatorSection", "ParallelSection"]
