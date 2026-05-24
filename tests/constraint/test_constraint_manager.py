import pytest

from femora.core.model import Model
from femora.components.constraint.sp_constraints import FixConstraint
from femora.components.constraint.mp_constraints import EqualDOF
from femora.core.constraint_manager import ConstraintManager
from femora.core.mp_constraint_manager import MPConstraintManager
from femora.core.sp_constraint_manager import SpConstraintManager


@pytest.fixture
def mesh_maker():
    mk = Model()
    mk.clear_model()
    return mk


def test_constraint_submanagers_have_no_legacy_lookup_names(mesh_maker):
    sp_manager = mesh_maker.constraint.sp
    mp_manager = mesh_maker.constraint.mp
    assert not hasattr(sp_manager, "get_constraint")
    assert not hasattr(sp_manager, "remove_constraint")
    assert not hasattr(mp_manager, "get_constraint")
    assert not hasattr(mp_manager, "remove_constraint")


def test_sp_constraint_manager_has_no_clear_all(mesh_maker):
    assert not hasattr(mesh_maker.constraint.sp, "clear_all")


def test_constraints_no_self_tagging():
    sp_constraint = FixConstraint(1, [1, 0, 0])
    mp_constraint = EqualDOF(1, [2], [1])
    assert sp_constraint.tag is None
    assert sp_constraint._owner is None
    assert mp_constraint.tag is None
    assert mp_constraint._owner is None


def test_manager_adds_and_tags(mesh_maker):
    sp_manager = mesh_maker.constraint.sp
    mp_manager = mesh_maker.constraint.mp
    sp_constraint = sp_manager.fix(1, [1, 0, 0])
    mp_constraint = mp_manager.equal_dof(1, [2], [1])
    assert sp_constraint.tag == 1
    assert mp_constraint.tag == 1
    assert sp_constraint._owner is sp_manager
    assert mp_constraint._owner is mp_manager
    assert sp_manager.get(sp_constraint.tag) is sp_constraint
    assert mp_manager.get(mp_constraint.tag) is mp_constraint


def test_manager_remove_and_retag(mesh_maker):
    sp_manager = mesh_maker.constraint.sp
    c1 = sp_manager.fix(1, [1, 0, 0])
    c2 = sp_manager.fix(2, [1, 0, 0])
    c3 = sp_manager.fix(3, [1, 0, 0])
    sp_manager.remove(c2.tag)
    assert c1.tag == 1
    assert c3.tag == 2
    assert c2.tag is None
    assert c2._owner is None


def test_manager_set_tag_start(mesh_maker):
    sp_manager = mesh_maker.constraint.sp
    c1 = sp_manager.fix(1, [1, 0, 0])
    sp_manager.set_tag_start(10)
    assert c1.tag == 10
    c2 = sp_manager.fix(2, [1, 0, 0])
    assert c2.tag == 11


def test_mp_manager_set_tag_start(mesh_maker):
    mp_manager = mesh_maker.constraint.mp
    c1 = mp_manager.equal_dof(1, [2], [1])
    mp_manager.set_tag_start(5)
    assert c1.tag == 5
    c2 = mp_manager.equal_dof(1, [3], [1])
    assert c2.tag == 6


def test_duplicate_ownership_rejected(mesh_maker):
    sp_manager = mesh_maker.constraint.sp
    constraint = FixConstraint(1, [1, 0, 0])
    constraint._owner = object()
    with pytest.raises(ValueError, match="already belongs to another manager"):
        sp_manager.add(constraint)


def test_duplicate_manager_creation_rejected(mesh_maker):
    with pytest.raises(ValueError, match="already owns a constraint manager"):
        ConstraintManager(mesh_maker)
    with pytest.raises(ValueError, match="already owns SP constraints"):
        SpConstraintManager(mesh_maker.constraint)
    with pytest.raises(ValueError, match="already owns MP constraints"):
        MPConstraintManager(mesh_maker.constraint)


def test_managers_require_mesh_maker():
    with pytest.raises(TypeError):
        ConstraintManager()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        SpConstraintManager(None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        MPConstraintManager(None)  # type: ignore[arg-type]
    mk = Model()
    mk.clear_model()
    with pytest.raises(TypeError):
        SpConstraintManager(mk)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        MPConstraintManager(mk)  # type: ignore[arg-type]


def test_mesh_maker_has_no_shadow_managers(mesh_maker):
    assert not hasattr(mesh_maker, "_sp_constraint_manager")
    assert not hasattr(mesh_maker, "_mp_constraint_manager")


def test_clear_model_resets_constraints(mesh_maker):
    mesh_maker.constraint.sp.fix(1, [1, 0, 0])
    mesh_maker.constraint.mp.equal_dof(1, [2], [1])
    assert len(mesh_maker.constraint.sp.get_all()) == 1
    assert len(mesh_maker.constraint.mp.get_all()) == 1
    mesh_maker.clear_model()
    assert len(mesh_maker.constraint.sp.get_all()) == 0
    assert len(mesh_maker.constraint.mp.get_all()) == 0
    new_constraint = mesh_maker.constraint.sp.fix(1, [1, 0, 0])
    assert new_constraint.tag == 1
