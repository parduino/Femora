import pytest
from femora.components.transformation.transformation import GeometricTransformation

class DummyTransformation(GeometricTransformation):
    def __init__(self, transf_type, dimension):
        super().__init__(transf_type, dimension)
    def has_joint_offsets(self):
        return False
    def to_tcl(self):
        return ""

@pytest.fixture(autouse=True)
def clear_transformations():
    GeometricTransformation.reset()
    yield
    GeometricTransformation.reset()

def test_transformation_sequential_tagging():
    t1 = DummyTransformation('Linear', 2)
    t2 = DummyTransformation('Linear', 2)
    t3 = DummyTransformation('Linear', 2)
    print(t1)
    assert t1.tag == 1
    assert t2.tag == 2
    assert t3.tag == 3

def test_transformation_custom_start_tag():
    GeometricTransformation.set_start_tag(100)
    t1 = DummyTransformation('Linear', 2)
    t2 = DummyTransformation('Linear', 2)
    assert t1.tag == 100
    assert t2.tag == 101

def test_transformation_tag_reset():
    t1 = DummyTransformation('Linear', 2)
    GeometricTransformation.clear_all_instances()
    GeometricTransformation.set_start_tag(50)
    t2 = DummyTransformation('Linear', 2)
    assert t2.tag == 50

def test_transformation_set_tag_start_after_some_created():
    GeometricTransformation.set_start_tag(1)
    t1 = DummyTransformation('Linear', 2)
    t2 = DummyTransformation('Linear', 2)
    GeometricTransformation.set_start_tag(200)
    t3 = DummyTransformation('Linear', 2)
    assert t1.tag == 200
    assert t2.tag == 201
    assert t3.tag == 202
    GeometricTransformation.set_start_tag(10)
    t4 = DummyTransformation('Linear', 2)
    assert t4.tag == 13

def test_transformation_tagging_with_deletions_and_start_tag_change():
    GeometricTransformation.set_start_tag(10)
    t1 = DummyTransformation('Linear', 2)  # tag 10
    t2 = DummyTransformation('Linear', 2)  # tag 11
    t3 = DummyTransformation('Linear', 2)  # tag 12
    assert t1.tag == 10
    assert t2.tag == 11
    assert t3.tag == 12
    t2.remove()
    GeometricTransformation.set_start_tag(104)
    t4 = DummyTransformation('Linear', 2)  # should get tag 104
    assert t4.tag == 106
    t1.remove()
    t3.remove()
    GeometricTransformation.set_start_tag(202)
    t5 = DummyTransformation('Linear', 2)  # should get tag 203
    assert t5.tag == 203