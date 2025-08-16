import pytest
from femora.components.Damping.dampingBase import DampingBase

class DummyDamping(DampingBase):
    def __init__(self):
        super().__init__()
    def get_values(self):
        return {}
    def update_values(self, **kwargs):
        pass
    def to_tcl(self):
        return ""

@pytest.fixture(autouse=True)
def clear_dampings():
    DampingBase.reset()
    yield
    DampingBase.reset()

def test_damping_sequential_tagging():
    d1 = DummyDamping()
    d2 = DummyDamping()
    d3 = DummyDamping()
    assert d1.tag == 1
    assert d2.tag == 2
    assert d3.tag == 3

def test_damping_custom_start_tag():
    DampingBase.set_tag_start(100)
    d1 = DummyDamping()
    d2 = DummyDamping()
    assert d1.tag == 100
    assert d2.tag == 101

def test_damping_tag_reset():
    d1 = DummyDamping()
    DampingBase.reset()
    DampingBase.set_tag_start(50)
    d2 = DummyDamping()
    assert d2.tag == 50

def test_damping_set_tag_start_after_some_created():
    DampingBase.set_tag_start(1)
    d1 = DummyDamping()
    d2 = DummyDamping()
    DampingBase.set_tag_start(200)
    # After retag, d1 and d2 should be 200, 201
    assert d1.tag == 200
    assert d2.tag == 201
    d3 = DummyDamping()
    assert d3.tag == 202
    DampingBase.set_tag_start(10)
    # After retag, all tags are reassigned starting from 10
    assert d1.tag == 10
    assert d2.tag == 11
    assert d3.tag == 12
    d4 = DummyDamping()
    assert d4.tag == 13

def test_damping_tagging_with_deletions_and_start_tag_change():
    DampingBase.set_tag_start(10)
    d1 = DummyDamping()  # tag 10
    d2 = DummyDamping()  # tag 11
    d3 = DummyDamping()  # tag 12
    assert d1.tag == 10
    assert d2.tag == 11
    assert d3.tag == 12
    DampingBase.remove_damping(d2.tag)
    # After removal, tags are reassigned: d1=10, d3=11
    assert d1.tag == 10
    assert d3.tag == 11
    DampingBase.set_tag_start(104)
    # After retag, d1=104, d3=105
    assert d1.tag == 104
    assert d3.tag == 105
    d4 = DummyDamping()  # should get tag 106
    assert d4.tag == 106
    DampingBase.remove_damping(d1.tag)
    DampingBase.remove_damping(d3.tag)
    DampingBase.set_tag_start(202)
    # only d4 is left, should get tag 202
    d5 = DummyDamping()  # should get tag 203
    assert d5.tag == 203 