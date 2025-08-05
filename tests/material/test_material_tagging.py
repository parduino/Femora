import pytest
from femora.components.Material.materialBase import Material

class DummyMaterial(Material):
    def __init__(self, material_type, material_name, user_name):
        super().__init__(material_type, material_name, user_name)
    @classmethod
    def get_parameters(cls):
        return []
    @classmethod
    def get_description(cls):
        return []
    def to_tcl(self):
        return ""

@pytest.fixture(autouse=True)
def clear_materials():
    Material.clear_all()
    yield
    Material.clear_all()

def test_material_sequential_tagging():
    m1 = DummyMaterial('uniaxialMaterial', 'Elastic', 'mat1')
    m2 = DummyMaterial('uniaxialMaterial', 'Elastic', 'mat2')
    m3 = DummyMaterial('uniaxialMaterial', 'Elastic', 'mat3')
    assert m1.tag == 1
    assert m2.tag == 2
    assert m3.tag == 3

def test_material_custom_start_tag():
    Material.set_tag_start(100)
    m1 = DummyMaterial('uniaxialMaterial', 'Elastic', 'matA')
    m2 = DummyMaterial('uniaxialMaterial', 'Elastic', 'matB')
    assert m1.tag == 100
    assert m2.tag == 101

def test_material_tag_reset():
    m1 = DummyMaterial('uniaxialMaterial', 'Elastic', 'matX')
    Material.clear_all()
    Material.set_tag_start(50)
    m2 = DummyMaterial('uniaxialMaterial', 'Elastic', 'matY')
    assert m2.tag == 50 

def test_material_set_tag_start_after_some_created():
    m1 = DummyMaterial('uniaxialMaterial', 'Elastic', 'mat1')
    m2 = DummyMaterial('uniaxialMaterial', 'Elastic', 'mat2')
    # Now set a new start tag higher than current
    Material.set_tag_start(200)
    m3 = DummyMaterial('uniaxialMaterial', 'Elastic', 'mat3')
    assert m1.tag == 200
    assert m2.tag == 201
    assert m3.tag == 202
    # If we set a start tag lower than the current, it should have no effect
    Material.set_tag_start(10)
    m4 = DummyMaterial('uniaxialMaterial', 'Elastic', 'mat4')
    assert m4.tag == 13

def test_material_tagging_with_deletions_and_start_tag_change():
    Material.set_tag_start(10)
    m1 = DummyMaterial('uniaxialMaterial', 'Elastic', 'mat1')  # tag 10
    m2 = DummyMaterial('uniaxialMaterial', 'Elastic', 'mat2')  # tag 11
    m3 = DummyMaterial('uniaxialMaterial', 'Elastic', 'mat3')  # tag 12
    assert m1.tag == 10
    assert m2.tag == 11
    assert m3.tag == 12
    # Delete m2
    Material.delete_material(m2.tag)
    # Now set a new start tag higher than current
    Material.set_tag_start(100)
    m4 = DummyMaterial('uniaxialMaterial', 'Elastic', 'mat4')  # should get tag 13 (next available)
    assert m4.tag == 102
    # Delete m1 and m3
    Material.delete_material(m1.tag)
    Material.delete_material(m3.tag)
    # Now set a new start tag higher than current
    Material.set_tag_start(200)
    m5 = DummyMaterial('uniaxialMaterial', 'Elastic', 'mat5')  # should get tag 200
    assert m5.tag == 201