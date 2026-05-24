import inspect

import pytest

from femora.core.model import Model
from femora.core.action_base import Action
from femora.core.process_manager import ProcessComponent, ProcessManager


@pytest.fixture
def mesh_maker():
    return Model(model_name="process_test")


def test_process_manager_lives_in_core():
    import femora.core.process_manager as process_manager_module

    assert process_manager_module.__name__ == "femora.core.process_manager"
    assert ProcessManager.__module__ == "femora.core.process_manager"
    assert ProcessComponent is not None


def test_process_manager_is_not_singleton(mesh_maker):
    manager_a = ProcessManager(mesh_maker=mesh_maker)
    manager_b = ProcessManager(mesh_maker=mesh_maker)
    assert manager_a is not manager_b


def test_process_manager_has_no_singleton_api():
    assert not hasattr(ProcessManager, "get_instance")
    assert not hasattr(ProcessManager, "_instance")


def test_mesh_maker_owns_process_manager(mesh_maker):
    assert isinstance(mesh_maker.process, ProcessManager)
    assert mesh_maker.process._mesh_maker is mesh_maker


def test_public_process_api_is_snake_case(mesh_maker):
    public_methods = {
        name
        for name, value in inspect.getmembers(mesh_maker.process, predicate=callable)
        if not name.startswith("_")
    }
    camel_case = {name for name in public_methods if any(ch.isupper() for ch in name)}
    assert camel_case == set()

    expected = {
        "add_step",
        "insert_step",
        "remove_step",
        "clear",
        "get_steps",
        "get_step",
        "to_tcl",
    }
    assert expected.issubset(public_methods)
    assert not hasattr(mesh_maker.process, "clear_steps")


def test_process_depends_on_core_action_base(mesh_maker):
    action = mesh_maker.actions.tcl("custom command")
    assert isinstance(action, Action)

    mesh_maker.process.add_step(action, description="Custom TCL")
    tcl = mesh_maker.process.to_tcl()
    assert "custom command" in tcl


def test_process_step_lifecycle(mesh_maker):
    action_a = mesh_maker.actions.reset()
    action_b = mesh_maker.actions.exit()

    mesh_maker.process.add_step(action_a, description="Reset")
    mesh_maker.process.insert_step(0, action_b, description="Exit first")
    assert len(mesh_maker.process) == 2
    assert mesh_maker.process.get_step(0)["description"] == "Exit first"

    assert mesh_maker.process.remove_step(0) is True
    assert len(mesh_maker.process) == 1

    mesh_maker.process.clear()
    assert len(mesh_maker.process) == 0
    assert mesh_maker.process.current_step == -1


def test_femora_module_does_not_expose_default_process_manager():
    import femora

    assert not hasattr(femora, "process")
