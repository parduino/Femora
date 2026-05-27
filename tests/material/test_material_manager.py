import pytest

from femora.core.model import Model


@pytest.fixture
def mesh_maker():
    mk = Model()
    mk.clear_model()
    return mk


def test_material_manager_has_no_get_material_alias(mesh_maker):
    assert not hasattr(mesh_maker.material, "get_material")
