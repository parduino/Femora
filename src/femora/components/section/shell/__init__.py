"""Shell and plate section components for Femora.

This subpackage contains ``section`` models used with shell and plate
elements, including homogeneous elastic membrane-plate response and
fiber-integrated nonlinear plate sections.

Normal runtime usage should go through ``model.section.shell.<factory>(...)`` on
a [Model][femora.core.model.Model] instance, for example
``model.section.shell.elastic_membrane_plate(...)`` or
``model.section.shell.plate_fiber(...)``.
"""

from femora.core.section_manager import SectionManager
from femora.components.section.shell.elastic_membrane_plate import ElasticMembranePlateSection
from femora.components.section.shell.plate_fiber import PlateFiberSection

SectionManager.register_section_type("ElasticMembranePlateSection", ElasticMembranePlateSection)
SectionManager.register_section_type("PlateFiber", PlateFiberSection)

__all__ = ["ElasticMembranePlateSection", "PlateFiberSection"]
