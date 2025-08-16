import pytest
from femora.components.Pattern.patternBase import Pattern

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
def clear_patterns():
    Pattern.reset()
    yield
    Pattern.reset()

def test_pattern_sequential_tagging():
    p1 = DummyPattern('Uniform')
    p2 = DummyPattern('Uniform')
    p3 = DummyPattern('Uniform')
    assert p1.tag == 1
    assert p2.tag == 2
    assert p3.tag == 3

def test_pattern_custom_start_tag():
    Pattern.set_tag_start(100)
    p1 = DummyPattern('Uniform')
    p2 = DummyPattern('Uniform')
    assert p1.tag == 100
    assert p2.tag == 101

def test_pattern_tag_reset():
    p1 = DummyPattern('Uniform')
    Pattern.reset()
    Pattern.set_tag_start(50)
    p2 = DummyPattern('Uniform')
    assert p2.tag == 50

def test_pattern_set_tag_start_after_some_created():
    Pattern.set_tag_start(1)
    p1 = DummyPattern('Uniform')
    p2 = DummyPattern('Uniform')
    Pattern.set_tag_start(200)
    # After retag, p1 and p2 should be 200, 201
    assert p1.tag == 200
    assert p2.tag == 201
    p3 = DummyPattern('Uniform')
    assert p3.tag == 202
    Pattern.set_tag_start(10)
    # After retag, all tags are reassigned starting from 10
    assert p1.tag == 10
    assert p2.tag == 11
    assert p3.tag == 12
    p4 = DummyPattern('Uniform')
    assert p4.tag == 13

def test_pattern_tagging_with_deletions_and_start_tag_change():
    Pattern.set_tag_start(10)
    p1 = DummyPattern('Uniform')  # tag 10
    p2 = DummyPattern('Uniform')  # tag 11
    p3 = DummyPattern('Uniform')  # tag 12
    assert p1.tag == 10
    assert p2.tag == 11
    assert p3.tag == 12
    Pattern.remove_pattern(p2.tag)
    # After removal, tags are reassigned: p1=10, p3=11
    assert p1.tag == 10
    assert p3.tag == 11
    Pattern.set_tag_start(104)
    # After retag, p1=104, p3=105
    assert p1.tag == 104
    assert p3.tag == 105
    p4 = DummyPattern('Uniform')  # should get tag 106
    assert p4.tag == 106
    Pattern.remove_pattern(p1.tag)
    Pattern.remove_pattern(p3.tag)
    Pattern.set_tag_start(202)
    # No patterns left, next should be 202
    p5 = DummyPattern('Uniform')  # should get tag 203
    assert p5.tag == 203 