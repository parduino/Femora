"""Specialized section components for Femora.

This subpackage contains purpose-built ``section`` models for isolation,
coupled bidirectional plasticity, and other specialized component behavior.

Normal runtime usage should go through ``model.section.special.<factory>(...)`` on
a [Model][femora.core.model.Model] instance, for example
``model.section.special.bidirectional(...)`` or
``model.section.special.isolator2spring(...)``.
"""

from femora.core.section_manager import SectionManager
from femora.components.section.special.bidirectional import BidirectionalSection
from femora.components.section.special.isolator2spring import Isolator2SpringSection

SectionManager.register_section_type("Bidirectional", BidirectionalSection)
SectionManager.register_section_type("Isolator2spring", Isolator2SpringSection)

__all__ = ["BidirectionalSection", "Isolator2SpringSection"]
