from __future__ import annotations

from typing import TYPE_CHECKING, Union

import numpy as np

from femora.core.action_base import Action
from femora.core.material_base import Material

if TYPE_CHECKING:
    from femora.core.model import Model


class WipeAction(Action):
    def to_tcl(self) -> str:
        return "wipe"


class WipeAnalysisAction(Action):
    def to_tcl(self) -> str:
        return "wipeAnalysis"


class ResetAction(Action):
    def to_tcl(self) -> str:
        return "reset"


class LoadConstAction(Action):
    def to_tcl(self) -> str:
        return "loadConst"


class ExitAction(Action):
    def to_tcl(self) -> str:
        return "exit"


class RemoveRecordersAction(Action):
    def to_tcl(self) -> str:
        return "remove recorders"


class SetTimeAction(Action):
    def __init__(self, pseudo_time: float):
        self.pseudo_time = pseudo_time

    def to_tcl(self) -> str:
        return f"setTime {self.pseudo_time}"


class TclAction(Action):
    def __init__(self, command: str):
        self.command = command

    def to_tcl(self) -> str:
        return self.command


class SetMaterialParameterAction(Action):
    def __init__(
        self,
        mesh_maker: "Model",
        material: Union[int, str, Material],
        parameter_name: str,
        parameter_value: Union[float, int, str, None] = None,
        element_tags: Union[list[int], None] = None,
    ):
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
        return self.mat.set_parameter(
            parameter_name=self.parameter_name,
            new_value=self.parameter_value,
            element_tags=self.element_tags,
        )


class UpdateMaterialStageToElasticAction(Action):
    def __init__(self, mesh_maker: "Model"):
        self._mesh_maker = mesh_maker

    def to_tcl(self) -> str:
        cmd = ""
        for mat in self._mesh_maker.material.get_all().values():
            tmp = mat.updateMaterialStage("Elastic")
            if tmp != "":
                cmd += tmp + "\n"
        return cmd


class UpdateMaterialStageToPlasticAction(Action):
    def __init__(self, mesh_maker: "Model"):
        self._mesh_maker = mesh_maker

    def to_tcl(self) -> str:
        cmd = ""
        for mat in self._mesh_maker.material.get_all().values():
            tmp = mat.updateMaterialStage("Plastic")
            if tmp != "":
                cmd += tmp + "\n"
        return cmd


class RemoveLoadPatternsAction(Action):
    def __init__(self, mesh_maker: "Model"):
        self._mesh_maker = mesh_maker

    def to_tcl(self) -> str:
        tags = sorted(int(tag) for tag in self._mesh_maker.pattern.get_all().keys())
        if not tags:
            return ""
        return "\n".join(f"remove loadPattern {tag}" for tag in tags)


SetMaterialParameter = SetMaterialParameterAction
