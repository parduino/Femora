"""Composite section components for Femora.

This subpackage contains section models that combine other sections or add
independent uniaxial responses to an existing section definition.

Normal runtime usage should go through ``model.section.composite.<factory>(...)``
on a [Model][femora.core.model.Model] instance, for example
``model.section.composite.aggregator(...)`` or
``model.section.composite.parallel(...)``.
"""

from femora.core.section_manager import SectionManager
from femora.components.section.composite.aggregator import AggregatorSection
from femora.components.section.composite.parallel import ParallelSection

SectionManager.register_section_type("Aggregator", AggregatorSection)
SectionManager.register_section_type("Parallel", ParallelSection)

__all__ = ["AggregatorSection", "ParallelSection"]
