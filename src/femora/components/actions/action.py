# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import numpy as np

from femora.core.action_base import Action
from femora.core.material_base import Material

if TYPE_CHECKING:
    from femora.core.model import Model


class WipeAction(Action):
    """Wipe action to reset OpenSees.

    WipeAction clears the entire OpenSees database, destroying all defined nodes,
    elements, materials, loads, and analysis objects. It resets the state to its
    original clean slate.

    Tcl form:
        ``wipe``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        action = model.actions.wipe()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self) -> None:
        """Create a WipeAction instance."""
        super().__init__()

    def to_tcl(self) -> str:
        """Render this action as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "wipe"


class WipeAnalysisAction(Action):
    """Wipe analysis action to clear the analysis state.

    WipeAnalysisAction clears the active analysis configuration in OpenSees,
    destroying the solution algorithm, constraint handler, numbering scheme,
    solver system, convergence test, and integrator. It is normally used to
    change analysis types (e.g., transition from static to transient).

    Tcl form:
        ``wipeAnalysis``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        action = model.actions.wipe_analysis()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self) -> None:
        """Create a WipeAnalysisAction instance."""
        super().__init__()

    def to_tcl(self) -> str:
        """Render this action as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "wipeAnalysis"


class ResetAction(Action):
    """Reset action to revert the model state.

    ResetAction resets the model state in OpenSees back to the state of the last
    committed converged step or initial state, clearing all un-converged trials.

    Tcl form:
        ``reset``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        action = model.actions.reset()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self) -> None:
        """Create a ResetAction instance."""
        super().__init__()

    def to_tcl(self) -> str:
        """Render this action as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "reset"


class LoadConstAction(Action):
    """Load constant action to lock gravity load levels.

    LoadConstAction freezes the current loading state of all active load patterns,
    making them constant for subsequent analysis steps. It also resets the model's
    pseudo-time back to 0.0, which is standard when transitioning from a gravity
    analysis to lateral/dynamic loading.

    Tcl form:
        ``loadConst``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        action = model.actions.load_const()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self) -> None:
        """Create a LoadConstAction instance."""
        super().__init__()

    def to_tcl(self) -> str:
        """Render this action as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "loadConst"


class ExitAction(Action):
    """Exit action to terminate OpenSees execution.

    ExitAction stops the active OpenSees simulation script, closes open files,
    flushes recorder output buffers, and terminates the OpenSees process cleanly.

    Tcl form:
        ``exit``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        action = model.actions.exit()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self) -> None:
        """Create an ExitAction instance."""
        super().__init__()

    def to_tcl(self) -> str:
        """Render this action as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "exit"


class RemoveRecordersAction(Action):
    """Remove recorders action to halt output monitoring.

    RemoveRecordersAction destroys all active recorder objects registered in the
    model, flushing and closing their output files to prevent further writing.

    Tcl form:
        ``remove recorders``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        action = model.actions.remove_recorders()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self) -> None:
        """Create a RemoveRecordersAction instance."""
        super().__init__()

    def to_tcl(self) -> str:
        """Render this action as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "remove recorders"


class SetTimeAction(Action):
    """Set time action to manually modify model pseudo-time.

    SetTimeAction sets the current pseudo-time of the OpenSees domain to a
    user-specified value. This is useful for coordinate time stepping, resetting
    load stages, or aligning independent time-histories.

    Tcl form:
        ``setTime <pseudo_time>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        action = model.actions.set_time(pseudo_time=10.0)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, pseudo_time: float):
        """Create a SetTimeAction.

        Args:
            pseudo_time: The new pseudo-time value to assign to the domain.
        """
        self.pseudo_time = pseudo_time

    def to_tcl(self) -> str:
        """Render this action as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"setTime {self.pseudo_time}"


class TclAction(Action):
    """Tcl action to execute raw custom Tcl scripts.

    TclAction passes an arbitrary raw string command directly into the exported
    OpenSees Tcl script. Use this to incorporate custom user logic, procedure calls,
    or OpenSees features not natively modeled in Femora components.

    Tcl form:
        `<command>`

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        action = model.actions.tcl(command="puts \\"Hello from OpenSees!\\"")
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, command: str):
        """Create a TclAction.

        Args:
            command: The raw Tcl command string to execute.
        """
        self.command = command

    def to_tcl(self) -> str:
        """Render this action as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return self.command


class SetMaterialParameterAction(Action):
    """Set material parameter action to dynamically update material state.

    SetMaterialParameterAction generates a sequence of OpenSees parameter updates to
    change properties of structural materials inside elements during an analysis sequence.
    This can be used to update plastic shear modulus, cohesion, or other custom material
    variables.

    Tcl form:
        ``parameter <tag> element <ele_tag> <parameter_name>`` and ``updateParameter <tag> <value>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Assumes a material named 'soil' has been added
        action = model.actions.set_material_parameter(
            material='soil',
            parameter_name='refShearModulus',
            parameter_value=40000.0,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        mesh_maker: "Model",
        material: Union[int, str, Material],
        parameter_name: str,
        parameter_value: Union[float, int, str, None] = None,
        element_tags: Union[list[int], None] = None,
    ):
        """Create a SetMaterialParameterAction.

        Args:
            mesh_maker: The parent Model instance.
            material: The target material by tag, name, or instance.
            parameter_name: The name of the parameter inside the material.
            parameter_value: The new value to set.
            element_tags: Explicit list of element IDs to apply the parameter update.
                If None, updates all elements assigned the target material in the model.

        Raises:
            ValueError: If the target material cannot be found or if mesh is not assembled
                when `element_tags` is None.
            TypeError: If the material argument is an invalid type.
        """
        try:
            if isinstance(material, int):
                self.mat = mesh_maker.material.get(material)
                if self.mat is None:
                    raise KeyError(material)
            elif isinstance(material, str):
                self.mat = mesh_maker.material.get_by_name(material)
                if self.mat is None:
                    raise KeyError(material)
            elif isinstance(material, Material):
                self.mat = material
            else:
                raise TypeError(f"material must be int, str, or Material, got {type(material)}")
        except (KeyError, TypeError) as exc:
            raise ValueError(f"Material '{material}' not found in MaterialManager.") from exc

        if element_tags is None:
            assembled_mesh = mesh_maker.assembled_mesh
            if assembled_mesh is None:
                raise ValueError(
                    "Assembled mesh is not available; assemble the model before setting material parameters."
                )
            mask = assembled_mesh.cell_data["MaterialTag"] == self.mat.tag
            elements = np.arange(assembled_mesh.n_cells)[mask]
            elements = elements + mesh_maker._start_ele_tag
            self.element_tags = elements.tolist()
        else:
            self.element_tags = element_tags

        self.parameter_name = parameter_name
        self.parameter_value = parameter_value

    def to_tcl(self) -> str:
        """Render this action as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return self.mat.set_parameter(
            parameter_name=self.parameter_name,
            new_value=self.parameter_value,
            element_tags=self.element_tags,
        )


class UpdateMaterialStageToElasticAction(Action):
    """Update material stage to elastic action.

    UpdateMaterialStageToElasticAction triggers the `updateMaterialStage` command
    for all registered model materials to transition them to their elastic stage,
    often used to establish clean initial geostatic stress conditions before plastic
    shearing begins.

    Tcl form:
        ``updateMaterialStage -material <tag> -stage 0``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        action = model.actions.update_material_stage_to_elastic()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, mesh_maker: "Model"):
        """Create an UpdateMaterialStageToElasticAction.

        Args:
            mesh_maker: The parent Model instance.
        """
        self._mesh_maker = mesh_maker

    def to_tcl(self) -> str:
        """Render this action as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = ""
        for mat in self._mesh_maker.material.get_all().values():
            tmp = mat.updateMaterialStage("Elastic")
            if tmp != "":
                cmd += tmp + "\n"
        return cmd


class UpdateMaterialStageToPlasticAction(Action):
    """Update material stage to plastic action.

    UpdateMaterialStageToPlasticAction triggers the `updateMaterialStage` command
    for all registered model materials to transition them to their plastic/nonlinear stage,
    enabling advanced elastoplastic response after initial elastic consolidation.

    Tcl form:
        ``updateMaterialStage -material <tag> -stage 1``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        action = model.actions.update_material_stage_to_plastic()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, mesh_maker: "Model"):
        """Create an UpdateMaterialStageToPlasticAction.

        Args:
            mesh_maker: The parent Model instance.
        """
        self._mesh_maker = mesh_maker

    def to_tcl(self) -> str:
        """Render this action as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = ""
        for mat in self._mesh_maker.material.get_all().values():
            tmp = mat.updateMaterialStage("Plastic")
            if tmp != "":
                cmd += tmp + "\n"
        return cmd


class RemoveLoadPatternsAction(Action):
    """Remove load patterns action.

    RemoveLoadPatternsAction removes all registered load patterns from the active OpenSees
    domain, ensuring subsequent time steps are not affected by legacy force patterns.

    Tcl form:
        ``remove loadPattern <tag>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        action = model.actions.remove_load_patterns()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, mesh_maker: "Model"):
        """Create a RemoveLoadPatternsAction.

        Args:
            mesh_maker: The parent Model instance.
        """
        self._mesh_maker = mesh_maker

    def to_tcl(self) -> str:
        """Render this action as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        tags = sorted(int(tag) for tag in self._mesh_maker.pattern.get_all().keys())
        if not tags:
            return ""
        return "\n".join(f"remove loadPattern {tag}" for tag in tags)


SetMaterialParameter = SetMaterialParameterAction
