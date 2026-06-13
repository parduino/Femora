# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

import pytest
from femora.core.model import Model
from femora.core.transformation_base import GeometricTransformation
from femora.core.transformation_manager import TransformationManager

class DummyTransformation(GeometricTransformation):
    def __init__(self, transf_type, dimension):
        super().__init__(transf_type, dimension)
    def has_joint_offsets(self):
        return False
    def to_tcl(self):
        return f"geomTransf {self.transformation_type} {self._require_tag()}"

@pytest.fixture(autouse=True)
def manager():
    mesh_maker = Model()
    mesh_maker.clear_model()
    transformation_manager = mesh_maker.transformation
    yield transformation_manager
    mesh_maker.clear_model()

def test_transformation_tag_is_none_until_managed(manager):
    t1 = DummyTransformation('Linear', 2)
    assert t1.tag is None
    manager.add(t1)
    assert t1.tag == 1

def test_transformation_sequential_tagging(manager):
    t1 = DummyTransformation('Linear', 2)
    t2 = DummyTransformation('Linear', 2)
    t3 = DummyTransformation('Linear', 2)
    manager.add(t1)
    manager.add(t2)
    manager.add(t3)
    assert t1.tag == 1
    assert t2.tag == 2
    assert t3.tag == 3

def test_transformation_custom_start_tag(manager):
    manager.set_tag_start(100)
    t1 = manager.add(DummyTransformation('Linear', 2))
    t2 = manager.add(DummyTransformation('Linear', 2))
    assert t1.tag == 100
    assert t2.tag == 101

def test_transformation_clear_removes_owner_and_tags(manager):
    t1 = manager.add(DummyTransformation('Linear', 2))
    assert t1._owner is manager
    manager.clear()
    assert t1.tag is None
    assert t1._owner is None

def test_transformation_tag_reset(manager):
    manager.add(DummyTransformation('Linear', 2))
    manager.clear()
    manager.set_tag_start(50)
    t2 = manager.add(DummyTransformation('Linear', 2))
    assert t2.tag == 50

def test_transformation_set_tag_start_after_some_created(manager):
    t1 = manager.add(DummyTransformation('Linear', 2))
    t2 = manager.add(DummyTransformation('Linear', 2))
    manager.set_tag_start(200)
    t3 = manager.add(DummyTransformation('Linear', 2))
    assert t1.tag == 200
    assert t2.tag == 201
    assert t3.tag == 202
    manager.set_tag_start(10)
    t4 = manager.add(DummyTransformation('Linear', 2))
    assert t4.tag == 13

def test_transformation_tagging_with_deletions_and_start_tag_change(manager):
    manager.set_tag_start(10)
    t1 = manager.add(DummyTransformation('Linear', 2))  # tag 10
    t2 = manager.add(DummyTransformation('Linear', 2))  # tag 11
    t3 = manager.add(DummyTransformation('Linear', 2))  # tag 12
    assert t1.tag == 10
    assert t2.tag == 11
    assert t3.tag == 12
    manager.remove(t2.tag)
    manager.set_tag_start(104)
    t4 = manager.add(DummyTransformation('Linear', 2))
    assert t1.tag == 104
    assert t3.tag == 105
    assert t4.tag == 106
    manager.remove(t1.tag)
    manager.remove(t3.tag)
    manager.set_tag_start(202)
    t5 = manager.add(DummyTransformation('Linear', 2))
    assert t5.tag == 203

def test_unmanaged_transformation_to_tcl_fails(manager):
    transformation = DummyTransformation('Linear', 2)
    with pytest.raises(ValueError, match="managed before rendering TCL"):
        transformation.to_tcl()
    manager.add(transformation)
    assert transformation.to_tcl() == "geomTransf Linear 1"

def test_adding_to_another_manager_fails(manager):
    transformation = manager.add(DummyTransformation('Linear', 2))
    with pytest.raises(ValueError, match="already owns a transformation manager"):
        TransformationManager(mesh_maker=Model())
    assert transformation._owner is manager
