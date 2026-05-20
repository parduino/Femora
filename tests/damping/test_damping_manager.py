import pytest
from femora.core.damping_base import Damping
from femora.core.damping_manager import DampingManager
from femora.components.damping.dampings import RayleighDamping
from femora.components.MeshMaker import MeshMaker

class DummyDamping(Damping):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def to_tcl(self):
        return ""

@pytest.fixture
def mesh_maker():
    mk = MeshMaker()
    mk.clear_model()
    return mk

def test_damping_no_self_tagging():
    d1 = DummyDamping()
    assert d1.tag is None
    assert d1._owner is None

def test_manager_adds_and_tags(mesh_maker):
    dm = mesh_maker.damping
    d1 = DummyDamping()
    dm.add(d1)
    assert d1.tag == 1
    assert d1._owner == dm
    assert dm.get(1) == d1

def test_manager_sequential_tagging(mesh_maker):
    dm = mesh_maker.damping
    d1 = dm.rayleigh(alphaM=0.05)
    d2 = dm.rayleigh(betaK=0.01)
    assert d1.tag == 1
    assert d2.tag == 2
    assert len(dm.get_all()) == 2

def test_manager_remove_and_retag(mesh_maker):
    dm = mesh_maker.damping
    d1 = dm.rayleigh(alphaM=0.05)
    d2 = dm.rayleigh(betaK=0.01)
    d3 = dm.rayleigh(alphaM=0.02)
    
    dm.remove(d2.tag)
    assert len(dm.get_all()) == 2
    assert d1.tag == 1
    assert d3.tag == 2
    assert d2.tag is None
    assert d2._owner is None

def test_manager_set_tag_start(mesh_maker):
    dm = mesh_maker.damping
    d1 = dm.rayleigh(alphaM=0.05)
    dm.set_tag_start(100)
    assert d1.tag == 100
    d2 = dm.rayleigh(betaK=0.01)
    assert d2.tag == 101

def test_duplicate_ownership_rejected(mesh_maker):
    dm1 = mesh_maker.damping
    d1 = DummyDamping()
    dm1.add(d1)
    with pytest.raises(ValueError, match="already owns a damping manager"):
        DampingManager(mesh_maker)

def test_clear_model_resets_damping(mesh_maker):
    dm = mesh_maker.damping
    dm.rayleigh(alphaM=0.05)
    assert len(dm.get_all()) == 1
    mesh_maker.clear_model()
    assert len(mesh_maker.damping.get_all()) == 0
    d2 = mesh_maker.damping.rayleigh(alphaM=0.05)
    assert d2.tag == 1
