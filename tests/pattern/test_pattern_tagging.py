import pytest
from femora.core.model import Model
from femora.core.pattern_base import Pattern

class DummyPattern(Pattern):
    def __init__(self, pattern_type):
        super().__init__(pattern_type)
    def to_tcl(self):
        return ""
    @staticmethod
    def get_parameters():
        return []
    def get_values(self):
        return {}
    def update_values(self, **kwargs):
        pass

@pytest.fixture(autouse=True)
def manager():
    mesh_maker = Model()
    mesh_maker.clear_model()
    yield mesh_maker.pattern
    mesh_maker.clear_model()

def test_pattern_sequential_tagging(manager):
    p1 = manager.add(DummyPattern('Uniform'))
    p2 = manager.add(DummyPattern('Uniform'))
    p3 = manager.add(DummyPattern('Uniform'))
    assert p1.tag == 1
    assert p2.tag == 2
    assert p3.tag == 3

def test_pattern_custom_start_tag(manager):
    manager.set_tag_start(100)
    p1 = manager.add(DummyPattern('Uniform'))
    p2 = manager.add(DummyPattern('Uniform'))
    assert p1.tag == 100
    assert p2.tag == 101

def test_pattern_tag_reset(manager):
    manager.add(DummyPattern('Uniform'))
    manager.clear()
    manager.set_tag_start(50)
    p2 = manager.add(DummyPattern('Uniform'))
    assert p2.tag == 50

def test_pattern_set_tag_start_after_some_created(manager):
    manager.set_tag_start(1)
    p1 = manager.add(DummyPattern('Uniform'))
    p2 = manager.add(DummyPattern('Uniform'))
    manager.set_tag_start(200)
    # After retag, p1 and p2 should be 200, 201
    assert p1.tag == 200
    assert p2.tag == 201
    p3 = manager.add(DummyPattern('Uniform'))
    assert p3.tag == 202
    manager.set_tag_start(10)
    # After retag, all tags are reassigned starting from 10
    assert p1.tag == 10
    assert p2.tag == 11
    assert p3.tag == 12
    p4 = manager.add(DummyPattern('Uniform'))
    assert p4.tag == 13

def test_pattern_tagging_with_deletions_and_start_tag_change(manager):
    manager.set_tag_start(10)
    p1 = manager.add(DummyPattern('Uniform'))  # tag 10
    p2 = manager.add(DummyPattern('Uniform'))  # tag 11
    p3 = manager.add(DummyPattern('Uniform'))  # tag 12
    assert p1.tag == 10
    assert p2.tag == 11
    assert p3.tag == 12
    manager.remove(p2.tag)
    # After removal, tags are reassigned: p1=10, p3=11
    assert p1.tag == 10
    assert p3.tag == 11
    manager.set_tag_start(104)
    # After retag, p1=104, p3=105
    assert p1.tag == 104
    assert p3.tag == 105
    p4 = manager.add(DummyPattern('Uniform'))  # should get tag 106
    assert p4.tag == 106
    manager.remove(p1.tag)
    manager.remove(p3.tag)
    manager.set_tag_start(202)
    # Existing p4 is retagged to 202, so the next tag should be 203.
    p5 = manager.add(DummyPattern('Uniform'))
    assert p5.tag == 203
