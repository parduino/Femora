import pytest

from femora.components.Material.materialBase import Material
from femora.components.Material.materialsOpenSees import Steel01Material


@pytest.fixture(autouse=True)
def clear_materials_registry():
    Material.clear_all()
    yield
    Material.clear_all()


def test_steel01_tcl_output_defaults():
    mat = Steel01Material(user_name="S1", Fy=355.0, E0=200000.0, b=0.01)
    tcl = mat.to_tcl()
    expected = f"uniaxialMaterial Steel01 {mat.tag} 355.0 200000.0 0.01; # S1"
    assert tcl == expected


def test_steel01_tcl_output_with_isotropic():
    mat = Steel01Material(user_name="S2", Fy=420.0, E0=210000.0, b=0.02, a1=0.1, a2=5.0, a3=0.2, a4=10.0)
    tcl = mat.to_tcl()
    expected = (
        f"uniaxialMaterial Steel01 {mat.tag} 420.0 210000.0 0.02 0.1 5.0 0.2 10.0; # S2"
    )
    assert tcl == expected


@pytest.mark.parametrize(
    "kwargs, msg",
    [
        (dict(E0=200000.0, b=0.01), 'Fy'),
        (dict(Fy=355.0, b=0.01), 'E0'),
        (dict(Fy=355.0, E0=200000.0), 'b'),
        (dict(Fy=-1.0, E0=200000.0, b=0.01), 'Fy'),
        (dict(Fy=355.0, E0=0.0, b=0.01), 'E0'),
        (dict(Fy=355.0, E0=200000.0, b=-0.1), 'b'),
        (dict(Fy=355.0, E0=200000.0, b=0.01, a1=-0.1), 'a1'),
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
        Steel01Material(user_name="BadIso2", Fy=355.0, E0=200000.0, b=0.01, a1=0.1, a2=1.0, a3=0.2)


