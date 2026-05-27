import pytest
from unittest.mock import MagicMock
from femora.core.section_base import Section
from femora.core.section_manager import SectionManager
from femora.core.model import Model
from femora.components.section.beam import ElasticSection
from femora.components.element.elastic_beam_column import ElasticBeamColumnElement
from femora.core.transformation_base import GeometricTransformation

class MockTransformation(GeometricTransformation):
    def __init__(self, tag=1):
        self.tag = tag
    def to_tcl(self):
        return f"geomTransf Linear {self.tag}"

class DummySection(Section):
    def __init__(self, section_type, section_name, user_name):
        super().__init__(section_type, section_name, user_name)
    def to_tcl(self): return f"section {self.section_name} {self._require_tag()}"

@pytest.fixture
def mesh_maker():
    # Use an explicit local Model instance for integration tests
    mm = Model()
    mm.clear_model()
    return mm

@pytest.fixture
def manager(mesh_maker):
    return mesh_maker.section

def test_unmanaged_section_has_no_tag():
    sec = DummySection('section', 'Dummy', 'sec1')
    assert sec.tag is None
    assert sec._owner is None
    with pytest.raises(ValueError, match="must be managed before rendering TCL"):
        sec.to_tcl()

def test_manager_assigns_sequential_tags(manager):
    s1 = DummySection('section', 'Dummy', 'sec1')
    s2 = DummySection('section', 'Dummy', 'sec2')
    manager.add(s1)
    manager.add(s2)
    assert s1.tag == 1
    assert s2.tag == 2
    assert s1._owner is manager
    assert s2._owner is manager

def test_set_tag_start(manager):
    manager.set_tag_start(100)
    s1 = manager.add(DummySection('section', 'Dummy', 'sec1'))
    s2 = manager.add(DummySection('section', 'Dummy', 'sec2'))
    assert s1.tag == 100
    assert s2.tag == 101
    
    manager.set_tag_start(200)
    assert s1.tag == 200
    assert s2.tag == 201

def test_remove_retags_correctly(manager):
    s1 = manager.add(DummySection('section', 'Dummy', 'sec1'))
    s2 = manager.add(DummySection('section', 'Dummy', 'sec2'))
    s3 = manager.add(DummySection('section', 'Dummy', 'sec3'))
    
    manager.remove('sec2')
    assert s1.tag == 1
    assert s3.tag == 2
    assert s2.tag is None
    assert s2._owner is None

def test_clear_clears_owner_and_tags(manager):
    s1 = manager.add(DummySection('section', 'Dummy', 'sec1'))
    manager.clear()
    assert s1.tag is None
    assert s1._owner is None
    assert len(manager.get_all()) == 0

def test_adding_to_another_manager_fails():
    # Use mocks to simulate two different Models and Managers
    mm1 = MagicMock(spec=Model)
    mm1.section = None
    manager1 = SectionManager(mesh_maker=mm1)
    mm1.section = manager1
    
    mm2 = MagicMock(spec=Model)
    mm2.section = None
    manager2 = SectionManager(mesh_maker=mm2)
    mm2.section = manager2
    
    sec = DummySection('section', 'Dummy', 'sec1')
    manager1.add(sec)
    
    with pytest.raises(ValueError, match="already belongs to another manager"):
        manager2.add(sec)

def test_manager_already_exists(mesh_maker):
    # mesh_maker fixture already has a .section manager.
    # Creating another one for the same mesh_maker should fail.
    with pytest.raises(RuntimeError, match="Model already owns a SectionManager"):
        SectionManager(mesh_maker=mesh_maker)

def test_duplicate_user_name_fails(manager):
    manager.add(DummySection('section', 'Dummy', 'sec1'))
    with pytest.raises(ValueError, match="already exists in this manager"):
        manager.add(DummySection('section', 'Dummy', 'sec1'))

def test_section_dependent_elements(mesh_maker):
    manager = mesh_maker.section
    sec = manager.add(ElasticSection(user_name='sec1', E=200e9, A=0.01, Iz=1e-4, Iy=1e-4, G=77e9, J=2e-4))
    
    # Need a transformation too
    transf = mesh_maker.transformation.transformation3d("Linear", 0, 0, 1)

    element = mesh_maker.element.beam.elastic(ndof=6, section='sec1', transformation=transf)
    
    assert element._section is sec
    assert element.get_section_tag() == sec.tag
    
    tcl = element.to_tcl(tag=1, nodes=[1, 2])
    assert f" {sec.tag} " in tcl
    assert f" {transf.tag} " in tcl


def test_unmanaged_section_material_resolution_fails():
    sec = DummySection('section', 'Dummy', 'sec1')
    with pytest.raises(ValueError, match="Cannot resolve material by tag or name"):
        sec.resolve_material("SteelMat")


def test_managed_section_material_resolution_by_name(mesh_maker):
    mat = mesh_maker.material.uniaxial.elastic(user_name="SteelMat", E=29000.0)
    sec = mesh_maker.section.beam.uniaxial(user_name="Axial", material="SteelMat", response_code="P")
    assert sec.material is mat


def test_unmanaged_section_reference_resolution_fails():
    sec = DummySection('section', 'Dummy', 'sec1')
    with pytest.raises(ValueError, match="Cannot resolve section by tag or name"):
        sec.resolve_section("other_sec")
