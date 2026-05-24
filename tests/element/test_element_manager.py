import pytest

from femora.components.MeshMaker import MeshMaker
from femora.components.material.nd import ElasticIsotropicMaterial
from femora.core.element_base import Element


@pytest.fixture
def mesh_maker():
    mk = MeshMaker()
    mk.clear_model()
    return mk


def test_element_manager_has_no_legacy_aliases(mesh_maker):
    em = mesh_maker.element
    assert not hasattr(em, "get_element")
    assert not hasattr(em, "get_all_elements")
    assert not hasattr(em, "clear_all_elements")
    assert not hasattr(em, "get_element_count")


def test_element_count_uses_len(mesh_maker):
    mat = mesh_maker.material.add(
        ElasticIsotropicMaterial(user_name="m", E=1.0, nu=0.3, rho=0.0)
    )
    assert len(mesh_maker.element) == 0
    mesh_maker.element.brick.std(ndof=3, material=mat)
    assert len(mesh_maker.element) == 1


def test_element_base_has_no_class_level_registry_helpers():
    legacy_helpers = ("get_all_elements", "get_element_by_tag", "delete_element", "clear_all_elements")
    for helper in legacy_helpers:
        assert not hasattr(Element, helper)
