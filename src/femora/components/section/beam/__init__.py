"""---
icon: material/view-stream-outline
---

Beam-oriented section components for Femora.

This subpackage contains ``section`` models commonly used with beam and
truss elements, including aggregate elastic properties, uniaxial response
wrappers, and built-in wide-flange fiber templates.

Normal runtime usage should go through ``model.section.beam.<factory>(...)`` on
a [Model][femora.core.model.Model] instance, for example
``model.section.beam.elastic(...)`` or ``model.section.beam.wf2d(...)``.
"""

from femora.core.section_manager import SectionManager
from femora.components.section.beam.elastic import ElasticSection
from femora.components.section.beam.uniaxial import UniaxialSection
from femora.components.section.beam.wf2d import WFSection2d

SectionManager.register_section_type("Elastic", ElasticSection)
SectionManager.register_section_type("Uniaxial", UniaxialSection)
SectionManager.register_section_type("WFSection2d", WFSection2d)

__all__ = ["ElasticSection", "UniaxialSection", "WFSection2d"]
