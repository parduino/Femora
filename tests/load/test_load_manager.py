# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

import pytest

from femora.core.model import Model
from femora.components.load.node_load import NodeLoad
from femora.components.load.element_load import ElementLoad
from femora.components.load.sp_load import SpLoad
from femora.core.load_base import Load
from femora.core.load_manager import LoadManager

REMOVED_HELPER_METHODS = ("get_parameters", "get_values", "validate", "update_values")


@pytest.fixture
def mesh_maker():
    mk = Model()
    mk.clear_model()
    return mk


def test_load_runtime_has_no_helper_api():
    for cls in (Load, NodeLoad, ElementLoad, SpLoad):
        for name in REMOVED_HELPER_METHODS:
            assert not hasattr(cls, name) or name not in cls.__dict__


@pytest.mark.parametrize(
    "factory, kwargs",
    [
        (NodeLoad, {"node_tag": 1, "values": [1.0, 0.0, 0.0]}),
        (ElementLoad, {"kind": "beamUniform", "ele_tags": [2], "params": {"Wy": -10.0}}),
        (SpLoad, {"node_tag": 3, "dof": 2, "value": -5.0}),
    ],
)
def test_unmanaged_load_has_no_tag_or_owner(factory, kwargs):
    load = factory(**kwargs)
    assert load.tag is None
    assert load._owner is None


def test_manager_adds_and_tags(mesh_maker):
    lm = mesh_maker.load
    load = NodeLoad(node_tag=1, values=[1.0, 0.0, 0.0])
    lm.add(load)
    assert load.tag == 1
    assert load._owner is lm
    assert lm.get(1) is load


def test_load_manager_has_no_legacy_ele_alias(mesh_maker):
    assert not hasattr(mesh_maker.load, "ele")


def test_manager_factory_methods(mesh_maker):
    lm = mesh_maker.load
    node = lm.node(node_tag=1, values=[1.0, 0.0, 0.0])
    ele = lm.element(kind="beamUniform", ele_tags=[2], params={"Wy": -10.0})
    sp = lm.sp(node_tag=3, dof=2, value=-5.0)
    assert node.tag == 1
    assert ele.tag == 2
    assert sp.tag == 3
    assert isinstance(node, NodeLoad)
    assert isinstance(ele, ElementLoad)
    assert isinstance(sp, SpLoad)


def test_manager_remove_and_retag(mesh_maker):
    lm = mesh_maker.load
    l1 = lm.node(node_tag=1, values=[1.0])
    l2 = lm.node(node_tag=2, values=[2.0])
    l3 = lm.node(node_tag=3, values=[3.0])
    lm.remove(l2.tag)
    assert len(lm.get_all()) == 2
    assert l1.tag == 1
    assert l3.tag == 2
    assert l2.tag is None
    assert l2._owner is None


def test_manager_set_tag_start(mesh_maker):
    lm = mesh_maker.load
    load = lm.node(node_tag=1, values=[1.0])
    lm.set_tag_start(100)
    assert load.tag == 100


def test_duplicate_manager_rejected(mesh_maker):
    with pytest.raises(ValueError, match="already owns a load manager"):
        LoadManager(mesh_maker)


def test_clear_model_resets_loads(mesh_maker):
    mesh_maker.load.node(node_tag=1, values=[1.0])
    assert len(mesh_maker.load.get_all()) == 1
    mesh_maker.clear_model()
    assert len(mesh_maker.load.get_all()) == 0
    load = mesh_maker.load.node(node_tag=2, values=[2.0])
    assert load.tag == 1


def test_plain_pattern_add_load_uses_mesh_maker_manager(mesh_maker):
    ts = mesh_maker.time_series.constant(factor=1.0)
    pattern = mesh_maker.pattern.plain(time_series=ts)
    load = pattern.add_load.node(node_tag=1, values=[0.0, -10.0, 0.0])
    assert load.tag == 1
    assert load._owner is mesh_maker.load
    assert load.pattern_tag == pattern.tag
    tcl = pattern.to_tcl()
    assert "load 1" in tcl
    assert "pattern Plain" in tcl


def test_plain_pattern_add_load_proxy_has_no_legacy_ele_alias(mesh_maker):
    ts = mesh_maker.time_series.constant(factor=1.0)
    pattern = mesh_maker.pattern.plain(time_series=ts)
    assert hasattr(pattern.add_load, "node")
    assert hasattr(pattern.add_load, "element")
    assert hasattr(pattern.add_load, "sp")
    assert not hasattr(pattern.add_load, "ele")


def test_unmanaged_pattern_add_load_raises(mesh_maker):
    from femora.components.pattern.plain_pattern import PlainPattern

    ts = mesh_maker.time_series.constant(factor=1.0)
    pattern = PlainPattern(ts)
    with pytest.raises(ValueError, match="Pattern must be managed before adding loads"):
        pattern.add_load.node(node_tag=1, values=[1.0])


def test_node_load_constructor_validation():
    with pytest.raises(ValueError, match="Either node_tag or node_mask"):
        NodeLoad(values=[1.0])
    with pytest.raises(ValueError, match="values must be a non-empty"):
        NodeLoad(node_tag=1, values=[])


def test_element_load_constructor_validation():
    with pytest.raises(ValueError, match="kind must be"):
        ElementLoad(kind="invalid", ele_tags=[1], params={"Wy": 1.0})
    with pytest.raises(ValueError, match="params.Wy is required"):
        ElementLoad(kind="beamUniform", ele_tags=[1], params={})


def test_sp_load_constructor_validation():
    with pytest.raises(ValueError, match="Either node_tag or node_mask"):
        SpLoad(dof=1, value=1.0)
