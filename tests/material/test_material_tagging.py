# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

"""Tests for the manager-owned material tagging architecture.

Each test uses an explicit local ``Model()`` instance and resets state via
``clear_model()``.
"""

import pytest

from femora.core.model import Model
from femora.core.material_base import Material


class DummyMaterial(Material):
    """Minimal concrete material for tagging tests."""

    def __init__(self, user_name: str):
        super().__init__("uniaxialMaterial", "Dummy", user_name)

    def to_tcl(self) -> str:
        return f"# dummy material {self._require_tag()} {self.user_name}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def manager():
    """Provide a fresh material manager via Model for each test."""
    mm = Model()
    mm.clear_model()
    yield mm.material
    mm.clear_model()


# ---------------------------------------------------------------------------
# Ownership and tag lifecycle
# ---------------------------------------------------------------------------

def test_material_tag_is_none_before_managed(manager):
    """tag must be None until the object is added to a manager."""
    m = DummyMaterial("mat1")
    assert m.tag is None


def test_material_owner_is_none_before_managed(manager):
    m = DummyMaterial("mat1")
    assert m._owner is None


def test_material_owner_set_on_add(manager):
    m = DummyMaterial("mat1")
    manager.add(m)
    assert m._owner is manager


def test_duplicate_user_name_rejected(manager):
    manager.add(DummyMaterial("mat1"))
    with pytest.raises(ValueError, match="user_name 'mat1' already exists"):
        manager.add(DummyMaterial("mat1"))


# ---------------------------------------------------------------------------
# Sequential tagging
# ---------------------------------------------------------------------------

def test_sequential_tagging(manager):
    m1 = manager.add(DummyMaterial("mat1"))
    m2 = manager.add(DummyMaterial("mat2"))
    m3 = manager.add(DummyMaterial("mat3"))
    assert m1.tag == 1
    assert m2.tag == 2
    assert m3.tag == 3


# ---------------------------------------------------------------------------
# Custom set_tag_start
# ---------------------------------------------------------------------------

def test_custom_start_tag(manager):
    manager.set_tag_start(100)
    m1 = manager.add(DummyMaterial("matA"))
    m2 = manager.add(DummyMaterial("matB"))
    assert m1.tag == 100
    assert m2.tag == 101


def test_set_tag_start_retags_existing(manager):
    m1 = manager.add(DummyMaterial("mat1"))
    m2 = manager.add(DummyMaterial("mat2"))
    manager.set_tag_start(200)
    m3 = manager.add(DummyMaterial("mat3"))
    assert m1.tag == 200
    assert m2.tag == 201
    assert m3.tag == 202


def test_set_tag_start_below_count_still_compacts(manager):
    """set_tag_start(10) with 3 objects → tags 10, 11, 12; next add → 13."""
    m1 = manager.add(DummyMaterial("mat1"))
    m2 = manager.add(DummyMaterial("mat2"))
    m3 = manager.add(DummyMaterial("mat3"))
    manager.set_tag_start(10)
    assert m1.tag == 10
    assert m2.tag == 11
    assert m3.tag == 12
    m4 = manager.add(DummyMaterial("mat4"))
    assert m4.tag == 13


def test_set_tag_start_invalid(manager):
    with pytest.raises(ValueError):
        manager.set_tag_start(0)


# ---------------------------------------------------------------------------
# clear()
# ---------------------------------------------------------------------------

def test_clear_removes_tags_and_owners(manager):
    m1 = manager.add(DummyMaterial("mat1"))
    m2 = manager.add(DummyMaterial("mat2"))
    manager.clear()
    assert m1.tag is None
    assert m1._owner is None
    assert m2.tag is None
    assert m2._owner is None
    assert len(manager) == 0


def test_tag_reset_after_clear(manager):
    manager.add(DummyMaterial("mat1"))
    manager.clear()
    m2 = manager.add(DummyMaterial("mat2"))
    assert m2.tag == 1


# ---------------------------------------------------------------------------
# remove() and compact retagging
# ---------------------------------------------------------------------------

def test_retagging_after_remove(manager):
    m1 = manager.add(DummyMaterial("mat1"))
    m2 = manager.add(DummyMaterial("mat2"))
    m3 = manager.add(DummyMaterial("mat3"))
    manager.remove(m2.tag)
    assert m1.tag == 1
    assert m3.tag == 2


def test_removed_material_tag_and_owner_cleared(manager):
    m = manager.add(DummyMaterial("mat1"))
    tag = m.tag
    manager.remove(tag)
    assert m.tag is None
    assert m._owner is None


def test_tagging_with_deletions_and_start_tag_change(manager):
    manager.set_tag_start(10)
    m1 = manager.add(DummyMaterial("mat1"))   # tag 10
    m2 = manager.add(DummyMaterial("mat2"))   # tag 11
    m3 = manager.add(DummyMaterial("mat3"))   # tag 12
    assert m1.tag == 10
    assert m2.tag == 11
    assert m3.tag == 12
    manager.remove(m2.tag)                    # compact → 10, 11
    manager.set_tag_start(100)
    m4 = manager.add(DummyMaterial("mat4"))   # compact → 100, 101; add → 102
    assert m4.tag == 102
    manager.remove(m1.tag)
    manager.remove(m3.tag)
    manager.set_tag_start(200)
    m5 = manager.add(DummyMaterial("mat5"))   # only m4 left → 200; next → 201
    assert m5.tag == 201


# ---------------------------------------------------------------------------
# add-to-another-manager rejection
# ---------------------------------------------------------------------------

def test_add_to_another_manager_rejected():
    mm1 = Model()
    mm1.clear_model()
    m = DummyMaterial("shared_mat")
    mm1.material.add(m)
    with pytest.raises(ValueError, match="already belongs to another manager"):
        original_owner = m._owner
        m._owner = object()
        try:
            mm1.material.add(m)
        finally:
            m._owner = original_owner


# ---------------------------------------------------------------------------
# to_tcl fails for unmanaged material
# ---------------------------------------------------------------------------

def test_to_tcl_fails_without_manager():
    m = DummyMaterial("unmanaged")
    with pytest.raises(ValueError, match="managed"):
        m.to_tcl()


# ---------------------------------------------------------------------------
# Model clear_model resets manager
# ---------------------------------------------------------------------------

def test_clear_model_resets_material_manager():
    mm = Model()
    mm.clear_model()
    mm.material.set_tag_start(50)
    mm.material.add(DummyMaterial("mat1"))
    mm.clear_model()
    # After clear_model the manager is empty and start tag is reset to 1
    assert len(mm.material) == 0
    m = mm.material.add(DummyMaterial("fresh"))
    assert m.tag == 1


def test_namespaced_material_factories(manager):
    nd_material = manager.nd.elastic_isotropic(user_name="soil", E=30e6, nu=0.3, rho=2000.0)
    uniaxial_material = manager.uniaxial.steel01(user_name="steel", Fy=355.0, E0=200000.0, b=0.01)

    assert nd_material.tag == 1
    assert uniaxial_material.tag == 2
    assert nd_material._owner is manager
    assert uniaxial_material._owner is manager


def test_namespaced_material_factories_accept_name_alias(manager):
    material = manager.nd.elastic_isotropic(name="soil", E=30e6, nu=0.3, rho=2000.0)
    assert material.user_name == "soil"
