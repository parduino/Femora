"""Section component package for Femora.

This package contains runtime section component classes that are registered
through [SectionManager][femora.core.section_manager.SectionManager] and
exported to OpenSees Tcl as ``section`` commands. Components are grouped into
beam, fiber, composite, shell, and special subpackages.

Normal runtime usage should go through a [Model][femora.core.model.Model]
instance and its section manager entry points, such as
``model.section.beam.*``, ``model.section.fiber.*``,
``model.section.composite.*``, ``model.section.shell.*``, and
``model.section.special.*``. Importing this package registers the bundled
section types with the manager.
"""

from femora.core.section_base import Section
from femora.core.section_manager import SectionManager
from femora.components.section.beam import *
from femora.components.section.composite import *
from femora.components.section.fiber import *
from femora.components.section.shell import *
from femora.components.section.special import *
