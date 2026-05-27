import pytest
from femora.core.damping_base import Damping
from femora.core.damping_manager import DampingManager
from femora.core.model import Model

class DummyDamping(Damping):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def to_tcl(self):
        return ""

@pytest.fixture
def manager():
    mm = Model()
    mm.clear_model()
    return mm.damping

def test_damping_sequential_tagging(manager):
    d1 = manager.add(DummyDamping())
    d2 = manager.add(DummyDamping())
    d3 = manager.add(DummyDamping())
    assert d1.tag == 1
    assert d2.tag == 2
    assert d3.tag == 3

def test_damping_custom_start_tag(manager):
    manager.set_tag_start(100)
    d1 = manager.add(DummyDamping())
    d2 = manager.add(DummyDamping())
    assert d1.tag == 100
    assert d2.tag == 101

def test_damping_tag_reset(manager):
    d1 = manager.add(DummyDamping())
    manager.clear()
    manager.set_tag_start(50)
    d2 = manager.add(DummyDamping())
    assert d2.tag == 50

def test_damping_set_tag_start_after_some_created(manager):
    manager.set_tag_start(1)
    d1 = manager.add(DummyDamping())
    d2 = manager.add(DummyDamping())
    manager.set_tag_start(200)
    # After retag, d1 and d2 should be 200, 201
    assert d1.tag == 200
    assert d2.tag == 201
    d3 = manager.add(DummyDamping())
    assert d3.tag == 202
    manager.set_tag_start(10)
    # After retag, all tags are reassigned starting from 10
    assert d1.tag == 10
    assert d2.tag == 11
    assert d3.tag == 12
    d4 = manager.add(DummyDamping())
    assert d4.tag == 13

def test_damping_tagging_with_deletions_and_start_tag_change(manager):
    manager.set_tag_start(10)
    d1 = manager.add(DummyDamping())  # tag 10
    d2 = manager.add(DummyDamping())  # tag 11
    d3 = manager.add(DummyDamping())  # tag 12
    assert d1.tag == 10
    assert d2.tag == 11
    assert d3.tag == 12
    manager.remove(d2.tag)
    # After removal, tags are reassigned: d1=10, d3=11
    assert d1.tag == 10
    assert d3.tag == 11
    manager.set_tag_start(104)
    # After retag, d1=104, d3=105
    assert d1.tag == 104
    assert d3.tag == 105
    d4 = manager.add(DummyDamping())  # should get tag 106
    assert d4.tag == 106
    manager.remove(d1.tag)
    manager.remove(d3.tag)
    manager.set_tag_start(202)
    # only d4 is left, should get tag 202
    d5 = manager.add(DummyDamping())  # should get tag 203
    assert d5.tag == 203
