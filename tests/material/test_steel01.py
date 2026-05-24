"""Tests for Steel01Material using the manager-owned architecture."""

import pytest

from femora.core.model import Model
from femora.components.material.uniaxial import Steel01Material


@pytest.fixture(autouse=True)
def manager():
    mm = Model()
    mm.clear_model()
    yield mm.material
    mm.clear_model()


# ---------------------------------------------------------------------------
# TCL output
# ---------------------------------------------------------------------------

def test_steel01_tcl_output_defaults(manager):
    mat = manager.add(Steel01Material(user_name="S1", Fy=355.0, E0=200000.0, b=0.01))
    tcl = mat.to_tcl()
    assert tcl == f"uniaxialMaterial Steel01 {mat.tag} 355.0 200000.0 0.01; # S1"


def test_steel01_tcl_output_with_isotropic(manager):
    mat = manager.add(
        Steel01Material(
            user_name="S2", Fy=420.0, E0=210000.0, b=0.02,
            a1=0.1, a2=5.0, a3=0.2, a4=10.0,
        )
    )
    tcl = mat.to_tcl()
    assert tcl == (
        f"uniaxialMaterial Steel01 {mat.tag} 420.0 210000.0 0.02 0.1 5.0 0.2 10.0; # S2"
    )


def test_steel01_tag_assigned_by_manager(manager):
    mat = manager.add(Steel01Material(user_name="S3", Fy=355.0, E0=200000.0, b=0.01))
    assert mat.tag == 1


def test_steel01_tag_is_none_before_add():
    mat = Steel01Material(user_name="S_unmanaged", Fy=355.0, E0=200000.0, b=0.01)
    assert mat.tag is None


def test_steel01_to_tcl_fails_without_manager():
    mat = Steel01Material(user_name="S_unmanaged", Fy=355.0, E0=200000.0, b=0.01)
    with pytest.raises(ValueError, match="managed"):
        mat.to_tcl()


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "kwargs, msg",
    [
        (dict(E0=200000.0, b=0.01), "Fy"),
        (dict(Fy=355.0, b=0.01), "E0"),
        (dict(Fy=355.0, E0=200000.0), "b"),
        (dict(Fy=-1.0, E0=200000.0, b=0.01), "Fy"),
        (dict(Fy=355.0, E0=0.0, b=0.01), "E0"),
        (dict(Fy=355.0, E0=200000.0, b=-0.1), "b"),
        (dict(Fy=355.0, E0=200000.0, b=0.01, a1=-0.1), "a1"),
    ],
)
def test_steel01_validation_errors(kwargs, msg):
    with pytest.raises(ValueError) as ei:
        Steel01Material(user_name="Bad", **kwargs)
    assert msg in str(ei.value)


def test_steel01_partial_isotropic_rejected():
    with pytest.raises(ValueError):
        Steel01Material(user_name="BadIso1", Fy=355.0, E0=200000.0, b=0.01, a1=0.1)
    with pytest.raises(ValueError):
        Steel01Material(
            user_name="BadIso2", Fy=355.0, E0=200000.0, b=0.01,
            a1=0.1, a2=1.0, a3=0.2,
        )


# ---------------------------------------------------------------------------
# Sequential tagging
# ---------------------------------------------------------------------------

def test_sequential_tagging(manager):
    m1 = manager.add(Steel01Material(user_name="S1", Fy=355.0, E0=200000.0, b=0.01))
    m2 = manager.add(Steel01Material(user_name="S2", Fy=420.0, E0=210000.0, b=0.02))
    assert m1.tag == 1
    assert m2.tag == 2
