import inspect

import pytest

from femora.components.actions.action import WipeAction
from femora.core.model import Model
from femora.core.action_base import Action
from femora.core.action_manager import ActionManager


@pytest.fixture
def mesh_maker():
    return Model(model_name="action_test")


def test_action_base_lives_in_core():
    import femora.core.action_base as action_base_module

    assert action_base_module.__name__ == "femora.core.action_base"
    assert Action.__module__ == "femora.core.action_base"


def test_action_manager_lives_in_core():
    import femora.core.action_manager as action_manager_module

    assert action_manager_module.__name__ == "femora.core.action_manager"
    assert ActionManager.__module__ == "femora.core.action_manager"


def test_concrete_actions_live_in_components():
    import femora.components.actions.action as action_module

    assert action_module.__name__ == "femora.components.actions.action"
    assert WipeAction.__module__ == "femora.components.actions.action"
    assert issubclass(WipeAction, Action)
    assert not hasattr(action_module, "ActionManager")


def test_action_manager_is_not_singleton(mesh_maker):
    manager_a = ActionManager(mesh_maker=mesh_maker)
    manager_b = ActionManager(mesh_maker=mesh_maker)
    assert manager_a is not manager_b


def test_mesh_maker_owns_action_manager(mesh_maker):
    assert isinstance(mesh_maker.actions, ActionManager)
    assert mesh_maker.actions._mesh_maker is mesh_maker


def test_action_manager_has_no_singleton_api():
    assert not hasattr(ActionManager, "get_instance")
    assert not hasattr(ActionManager, "_instance")


def test_public_action_api_is_snake_case(mesh_maker):
    public_methods = {
        name
        for name, value in inspect.getmembers(mesh_maker.actions, predicate=callable)
        if not name.startswith("_") and name != "clear"
    }
    camel_case = {name for name in public_methods if any(ch.isupper() for ch in name)}
    assert camel_case == set()

    expected = {
        "wipe",
        "wipe_analysis",
        "reset",
        "load_const",
        "exit",
        "remove_recorders",
        "set_time",
        "tcl",
        "set_material_parameter",
        "update_material_stage_to_elastic",
        "update_material_stage_to_plastic",
        "remove_load_patterns",
    }
    assert expected.issubset(public_methods)


def test_action_factory_tcl_outputs(mesh_maker):
    assert mesh_maker.actions.wipe().to_tcl() == "wipe"
    assert mesh_maker.actions.wipe_analysis().to_tcl() == "wipeAnalysis"
    assert mesh_maker.actions.reset().to_tcl() == "reset"
    assert mesh_maker.actions.load_const().to_tcl() == "loadConst"
    assert mesh_maker.actions.exit().to_tcl() == "exit"
    assert mesh_maker.actions.remove_recorders().to_tcl() == "remove recorders"
    assert mesh_maker.actions.set_time(1.5).to_tcl() == "setTime 1.5"
    assert mesh_maker.actions.tcl("custom command").to_tcl() == "custom command"


def test_set_material_parameter_uses_mesh_maker_not_global_singleton(mesh_maker):
    mat = mesh_maker.material.nd.elastic_isotropic(user_name="mat", E=1.0, nu=0.3, rho=1.0)
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    mesh_maker.meshpart.volume.uniform_rectangular_grid(
        user_name="block",
        element=ele,
        x_min=0.0,
        x_max=1.0,
        y_min=0.0,
        y_max=1.0,
        z_min=0.0,
        z_max=1.0,
        nx=1,
        ny=1,
        nz=1,
    )
    mesh_maker.assembler.create_section(meshparts=["block"], num_partitions=1, merge_points=False)
    mesh_maker.assembler.assemble(merge_points=False)

    assert not hasattr(Model, "get_instance")

    action = mesh_maker.actions.set_material_parameter(mat, "E", 2.0)
    assert len(action.element_tags) == mesh_maker.assembled_mesh.n_cells
    assert isinstance(action.to_tcl(), str)


def test_femora_module_does_not_expose_default_action_manager():
    import femora

    assert not hasattr(femora, "actions")


def test_update_material_stage_actions_use_mesh_maker(mesh_maker):
    mesh_maker.material.nd.elastic_isotropic(user_name="mat", E=1.0, nu=0.3, rho=1.0)
    assert not hasattr(Model, "get_instance")

    elastic = mesh_maker.actions.update_material_stage_to_elastic()
    plastic = mesh_maker.actions.update_material_stage_to_plastic()
    assert isinstance(elastic.to_tcl(), str)
    assert isinstance(plastic.to_tcl(), str)
