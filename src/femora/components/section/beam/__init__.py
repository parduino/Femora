"""Beam-oriented section types."""

from femora.core.section_manager import SectionManager
from femora.components.section.beam.elastic import ElasticSection
from femora.components.section.beam.uniaxial import UniaxialSection
from femora.components.section.beam.wf2d import WFSection2d

SectionManager.register_section_type("Elastic", ElasticSection)
SectionManager.register_section_type("Uniaxial", UniaxialSection)
SectionManager.register_section_type("WFSection2d", WFSection2d)

__all__ = ["ElasticSection", "UniaxialSection", "WFSection2d"]
