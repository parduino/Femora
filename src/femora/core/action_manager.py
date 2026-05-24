from __future__ import annotations

from typing import TYPE_CHECKING, Union

from femora.components.actions.action import (
    ExitAction,
    LoadConstAction,
    RemoveLoadPatternsAction,
    RemoveRecordersAction,
    ResetAction,
    SetMaterialParameterAction,
    SetTimeAction,
    TclAction,
    UpdateMaterialStageToElasticAction,
    UpdateMaterialStageToPlasticAction,
    WipeAction,
    WipeAnalysisAction,
)
from femora.core.material_base import Material

if TYPE_CHECKING:
    from femora.core.model import Model


class ActionManager:
    """Model-owned factory for lightweight TCL-emitting actions."""

    def __init__(self, mesh_maker: "Model"):
        from femora.core.model import Model as ModelClass

        if not isinstance(mesh_maker, ModelClass):
            raise TypeError("mesh_maker must be a Model instance")
        self._mesh_maker = mesh_maker

    def wipe(self) -> WipeAction:
        return WipeAction()

    def wipe_analysis(self) -> WipeAnalysisAction:
        return WipeAnalysisAction()

    def reset(self) -> ResetAction:
        return ResetAction()

    def load_const(self) -> LoadConstAction:
        return LoadConstAction()

    def exit(self) -> ExitAction:
        return ExitAction()

    def remove_recorders(self) -> RemoveRecordersAction:
        return RemoveRecordersAction()

    def set_time(self, pseudo_time: float) -> SetTimeAction:
        return SetTimeAction(pseudo_time)

    def tcl(self, command: str) -> TclAction:
        return TclAction(command)

    def set_material_parameter(
        self,
        material: Union[int, str, Material],
        parameter_name: str,
        parameter_value: Union[float, int, str, None] = None,
        element_tags: Union[list[int], None] = None,
    ) -> SetMaterialParameterAction:
        return SetMaterialParameterAction(
            self._mesh_maker,
            material,
            parameter_name,
            parameter_value,
            element_tags,
        )

    def update_material_stage_to_elastic(self) -> UpdateMaterialStageToElasticAction:
        return UpdateMaterialStageToElasticAction(self._mesh_maker)

    def update_material_stage_to_plastic(self) -> UpdateMaterialStageToPlasticAction:
        return UpdateMaterialStageToPlasticAction(self._mesh_maker)

    def remove_load_patterns(self) -> RemoveLoadPatternsAction:
        return RemoveLoadPatternsAction(self._mesh_maker)

    def clear(self) -> None:
        """No-op; actions are stateless factories."""
        return None
