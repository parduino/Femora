import inspect

import pytest

from femora.components.MeshMaker import MeshMaker
from femora.components.region.regions import GlobalRegion
from femora.core.region_manager import RegionManager


@pytest.fixture
def mesh_maker():
    mk = MeshMaker()
    mk.clear_model()
    return mk


def test_region_manager_has_no_global_region_method():
    assert not inspect.isfunction(getattr(RegionManager, "GlobalRegion", None))


def test_global_region_property(mesh_maker):
    rm = mesh_maker.region
    global_region = rm.global_region
    assert isinstance(global_region, GlobalRegion)
    assert global_region.tag == 0
    assert rm.get(0) is global_region


def test_global_region_survives_clear(mesh_maker):
    rm = mesh_maker.region
    before = rm.global_region
    rm.node(user_name="nr1")
    rm.clear()
    after = rm.global_region
    assert after.tag == 0
    assert rm.get(0) is after
    assert after is not before


def test_duplicate_region_manager_rejected(mesh_maker):
    with pytest.raises(ValueError, match="already owns a region manager"):
        RegionManager(mesh_maker)
