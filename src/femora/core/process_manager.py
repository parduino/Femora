# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Union
import weakref

from femora.components.analysis.analysis import Analysis
from femora.core.action_base import Action
from femora.core.constraint_base import MPConstraint, SPConstraint
from femora.core.pattern_base import Pattern
from femora.core.recorder_base import Recorder

if TYPE_CHECKING:
    from femora.core.model import Model

ProcessComponent = Union[SPConstraint, MPConstraint, Pattern, Recorder, Analysis, Action]


class ProcessManager:
    """Model-owned manager for ordered analysis/process steps."""

    def __init__(self, mesh_maker: "Model"):
        from femora.core.model import Model as ModelClass

        if not isinstance(mesh_maker, ModelClass):
            raise TypeError("mesh_maker must be a Model instance")
        self._mesh_maker = mesh_maker
        self.steps: List[Dict] = []
        self.current_step = -1

    def __iter__(self):
        return iter(self.steps)

    def __len__(self):
        return len(self.steps)

    def add_step(
        self,
        component: Union[ProcessComponent, List[ProcessComponent]],
        description: str = "",
    ) -> int:
        if isinstance(component, list):
            last_index = -1
            for comp in component:
                last_index = self.add_step(comp, description)
            return last_index

        component_ref = self._store_component_ref(component)

        step = {
            "component": component_ref,
            "description": description,
        }

        self.steps.append(step)
        return len(self.steps) - 1

    def insert_step(
        self,
        index: int,
        component: Union[ProcessComponent, List[ProcessComponent]],
        description: str = "",
    ) -> bool:
        if isinstance(component, list):
            success = True
            for comp in reversed(component):
                success = success and self.insert_step(index, comp, description)
            return success

        if index < 0:
            index += len(self.steps) + 1

        if 0 <= index <= len(self.steps):
            component_ref = self._store_component_ref(component)

            step = {
                "component": component_ref,
                "description": description,
            }

            self.steps.insert(index, step)

            if index <= self.current_step:
                self.current_step += 1

            return True
        return False

    def remove_step(self, index: int) -> bool:
        if 0 <= index < len(self.steps):
            del self.steps[index]

            if index <= self.current_step:
                self.current_step -= 1

            return True
        return False

    def clear(self) -> None:
        self.steps.clear()
        self.current_step = -1

    def get_steps(self) -> List[Dict]:
        return self.steps

    def get_step(self, index: int) -> Optional[Dict]:
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None

    def to_tcl(self) -> str:
        tcl_script = ""
        for step in self.steps:
            component = step["component"]
            if isinstance(component, weakref.ref):
                component = component()
            description = step["description"]
            tcl_script += f"# {description} ======================================\n\n"
            tcl_script += f"{component.to_tcl()}\n\n\n"
        return tcl_script

    @staticmethod
    def _store_component_ref(component: ProcessComponent):
        if isinstance(component, Action):
            return component
        if isinstance(
            component,
            (SPConstraint, MPConstraint, Pattern, Recorder, Analysis),
        ):
            return weakref.ref(component)
        raise TypeError(
            f"Invalid component type: {type(component)}. Must be one of the allowed types."
        )
