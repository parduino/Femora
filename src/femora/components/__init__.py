
"""---
icon: material/puzzle-outline
---

Femora components package.

The `components` package is the concrete modeling surface of Femora. It
contains the runtime objects that represent the engineering choices a user
actually makes when building a model: materials, elements, sections, loads,
patterns, recorders, damping models, transformations, regions, analyses, and
related families.

In normal use, these objects are usually created through a
[`Model`][femora.core.model.Model] instance and its manager entry points rather
than by importing component classes directly. For example, users typically work
through paths such as `model.material...`, `model.element...`,
`model.section...`, `model.pattern...`, or `model.analysis...`. The component
pages explain what each concrete object represents and how it is used in a
simulation.

The package is organized by modeling concept. Some families describe physical
behavior, such as `material`, `section`, and `element`. Others describe loading
and excitation, such as `load`, `time_series`, `ground_motion`, and `pattern`.
Others capture analysis, output, and model scoping behavior, such as
`analysis`, `recorder`, `region`, `constraint`, and `damping`.

The `components` package should be read together with the `core` reference.
The component layer answers the question “what object represents this modeling
concept?” The `core` layer answers “how does Femora create, own, register,
tag, and coordinate that object internally?”

!!! tip "Where to start"
    If you are trying to find the right object to model something, start in
    `components`. If you are trying to understand ownership rules, manager
    behavior, caching, tagging, or orchestration, move from the relevant
    component family into the related page in `core`.

"""

from __future__ import annotations

import sys


def _install_partitioner_case_alias() -> None:
	try:
		from . import partitioner as _partitioner_pkg
		from .partitioner import partitioner as _partitioner_mod
	except Exception:
		return

	sys.modules.setdefault(__name__ + ".Partitioner", _partitioner_pkg)
	sys.modules.setdefault(__name__ + ".Partitioner.partitioner", _partitioner_mod)


_install_partitioner_case_alias()

