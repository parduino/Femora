# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from pathlib import Path
import re

import pytest

from femora.core.model import Model


def _source_has_model_get_instance_call(source: str) -> bool:
    stripped = re.sub(r'(["\']).*?\1', "", source, flags=re.DOTALL)
    return bool(re.search(r"\bModel\.get_instance\s*\(", stripped))


@pytest.fixture
def mesh_maker():
    model = Model()
    model.clear_model()
    return model


def test_model_construction_creates_distinct_instances():
    model_a = Model(model_name="a")
    model_b = Model(model_name="b")
    assert model_a is not model_b
    assert model_a.material is not model_b.material
    assert model_a.assembler._mesh_maker is model_a
    assert model_b.assembler._mesh_maker is model_b


def test_non_gui_runtime_has_no_model_get_instance_usage():
    violations = []
    for path in Path("src/femora").rglob("*.py"):
        rel = path.relative_to("src/femora").as_posix()
        if rel.startswith("gui/"):
            continue
        source = path.read_text(encoding="utf-8")
        if _source_has_model_get_instance_call(source):
            violations.append(rel)
        if "MeshMaker" in source:
            violations.append(rel)
        if "def gui(" in source:
            violations.append(rel)
    assert violations == []


def test_mask_to_tags_uses_model_owned_tag_start(mesh_maker):
    import femora.components.material.nd  # noqa: F401
    import femora.components.element.std_brick  # noqa: F401

    mesh_maker.set_nodetag_start(100)
    mesh_maker.set_eletag_start(200)
    mat = mesh_maker.material.nd.elastic_isotropic(user_name="mat", E=1.0, nu=0.3, rho=1.0)
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    mesh_maker.meshpart.volume.uniform_rectangular_grid(
        user_name="block",
        element=ele,
        x_min=0.0,
        x_max=1.0,
        y_min=0.0,
        y_max=1.0,
        z_min=0.0,
        z_max=1.0,
        nx=1,
        ny=1,
        nz=1,
    )
    mesh_maker.assembler.create_section(meshparts=["block"], num_partitions=1, merge_points=False)
    mesh_maker.assembler.assemble(merge_points=False)

    node_tags = mesh_maker.mask.nodes.to_tags()
    index = mesh_maker.mask._require_index()
    assert index.node_tag_start == 100
    assert index.element_tag_start == 200
    assert node_tags[0] == 100
    assert mesh_maker.mask.elements.to_tags()[0] == 200 + int(index.element_ids[0])
