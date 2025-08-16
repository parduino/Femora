import pytest

from femora.components.Material.materialBase import Material
from femora.components.Material.materialsOpenSees import PressureDependMultiYieldMaterial


@pytest.fixture(autouse=True)
def clear_materials_registry():
    Material.clear_all()
    yield
    Material.clear_all()


def base_params():
    return dict(
        nd=3,
        rho=2.0,
        refShearModul=1.0e5,
        refBulkModul=3.0e5,
        frictionAng=37.0,
        peakShearStra=0.1,
        refPress=80.0,
        pressDependCoe=0.5,
        PTAng=27.0,
        contrac=0.05,
        dilat1=0.6,
        dilat2=3.0,
        liquefac1=5.0,
        liquefac2=0.003,
        liquefac3=1.0,
        noYieldSurf=20,
        e=0.55,
        cs1=0.9,
        cs2=0.02,
        cs3=0.7,
        pa=101.0,
        c=0.3,
    )


def test_pdm_basic_auto_surfaces_to_tcl():
    params = base_params()
    mat = PressureDependMultiYieldMaterial(user_name="SoilAuto", **params)
    tcl = mat.to_tcl()
    assert "nDMaterial PressureDependMultiYield" in tcl
    # Exact expected TCL string
    expected = (
        f"nDMaterial PressureDependMultiYield {mat.tag} 3 2.0 100000.0 300000.0 37.0 0.1 80.0 0.5 27.0 "
        "0.05 0.6 3.0 5.0 0.003 1.0 noYieldSurf=20 e=0.55 cs1=0.9 cs2=0.02 cs3=0.7 pa=101.0 c=0.3; # SoilAuto"
    )
    assert tcl == expected


def test_pdm_negative_surfaces_with_flat_pairs():
    params = base_params()
    params.update(noYieldSurf=-2)
    # two pairs => 4 numbers
    params.update(pairs=[0.0001, 1.0, 0.01, 0.8])
    mat = PressureDependMultiYieldMaterial(user_name="SoilPairsFlat", **params)
    tcl = mat.to_tcl()
    expected = (
        f"nDMaterial PressureDependMultiYield {mat.tag} 3 2.0 100000.0 300000.0 37.0 0.1 80.0 0.5 27.0 "
        "0.05 0.6 3.0 5.0 0.003 1.0 noYieldSurf=-2 0.0001 1.0 0.01 0.8 "
        "e=0.55 cs1=0.9 cs2=0.02 cs3=0.7 pa=101.0 c=0.3; # SoilPairsFlat"
    )
    assert tcl == expected


def test_pdm_negative_surfaces_with_tuple_pairs():
    params = base_params()
    params.update(noYieldSurf=-3)
    params.update(pairs=[(0.0001, 1.0), (0.001, 0.95), (0.01, 0.8)])
    mat = PressureDependMultiYieldMaterial(user_name="SoilPairsTuples", **params)
    tcl = mat.to_tcl()
    expected = (
        f"nDMaterial PressureDependMultiYield {mat.tag} 3 2.0 100000.0 300000.0 37.0 0.1 80.0 0.5 27.0 "
        "0.05 0.6 3.0 5.0 0.003 1.0 noYieldSurf=-3 0.0001 1.0 0.001 0.95 0.01 0.8 "
        "e=0.55 cs1=0.9 cs2=0.02 cs3=0.7 pa=101.0 c=0.3; # SoilPairsTuples"
    )
    assert tcl == expected


@pytest.mark.parametrize(
    "bad_params, error_msg",
    [
        (dict(nd=4), "nd"),
        (dict(noYieldSurf=0), "noYieldSurf"),
        (dict(noYieldSurf=-2), "pairs"),  # missing pairs
    ],
)
def test_pdm_validation_errors_minimal(bad_params, error_msg):
    params = base_params()
    params.update(bad_params)
    # Remove pairs if any residual
    params.pop('pairs', None)
    with pytest.raises(ValueError) as ei:
        PressureDependMultiYieldMaterial(user_name="BadSoil", **params)
    assert error_msg in str(ei.value)


def test_pdm_pairs_length_validation():
    params = base_params()
    params.update(noYieldSurf=-2)
    # Wrong number of values (3 not 4)
    params.update(pairs=[0.0001, 1.0, 0.01])
    with pytest.raises(ValueError):
        PressureDependMultiYieldMaterial(user_name="BadPairsLen", **params)


def test_pdm_pairs_value_ranges():
    params = base_params()
    params.update(noYieldSurf=-1)
    # Invalid Gs (>1)
    params.update(pairs=[0.0001, 1.2])
    with pytest.raises(ValueError):
        PressureDependMultiYieldMaterial(user_name="BadPairsRange", **params)


