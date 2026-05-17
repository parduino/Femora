"""Shell and plate section types."""

from femora.core.section_manager import SectionManager
from femora.components.section.shell.elastic_membrane_plate import ElasticMembranePlateSection
from femora.components.section.shell.plate_fiber import PlateFiberSection

SectionManager.register_section_type("ElasticMembranePlateSection", ElasticMembranePlateSection)
SectionManager.register_section_type("PlateFiber", PlateFiberSection)

__all__ = ["ElasticMembranePlateSection", "PlateFiberSection"]
