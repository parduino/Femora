# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from pathlib import Path

import pytest

import femora.components.material.nd  # noqa: F401 — register material types
import femora.components.element.std_brick  # noqa: F401 — register element types

from femora.core.assembler import Assembler as CoreAssembler, AssemblySection
from femora.core.model import Model


@pytest.fixture
def mesh_maker():
    mk = Model()
    mk.clear_model()
    mk.assembler.clear()
    mk.assembler.delete_assembled_mesh()
    return mk


def _make_brick_meshpart(mesh_maker, user_name: str):
    mat = mesh_maker.material.nd.elastic_isotropic(user_name=f"mat_{user_name}", E=1.0, nu=0.3, rho=1.0)
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    mesh_maker.meshpart.volume.uniform_rectangular_grid(
        user_name=user_name,
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


def test_mesh_maker_constructs_core_assembler(mesh_maker):
    assert type(mesh_maker.assembler) is CoreAssembler


def test_assembly_section_source_does_not_self_register_via_singleton():
    source = Path("src/femora/core/assembler.py").read_text(encoding="utf-8")
    section_source = source.split("class AssemblySection:", 1)[1]
    assert "Assembler.get_instance()" not in section_source


def test_create_section_registers_section_on_assembler(mesh_maker):
    _make_brick_meshpart(mesh_maker, "block_a")
    _make_brick_meshpart(mesh_maker, "block_b")

    section_a = mesh_maker.assembler.create_section(meshparts=["block_a"], num_partitions=1, merge_points=False)
    section_b = mesh_maker.assembler.create_section(meshparts=["block_b"], num_partitions=1, merge_points=False)

    assert section_a.tag == 1
    assert section_b.tag == 2
    assert mesh_maker.assembler.get(1) is section_a
    assert mesh_maker.assembler.get(2) is section_b
    assert set(mesh_maker.assembler.get_all().values()) == {section_a, section_b}


def test_remove_retags_remaining_sections(mesh_maker):
    _make_brick_meshpart(mesh_maker, "block_a")
    _make_brick_meshpart(mesh_maker, "block_b")
    _make_brick_meshpart(mesh_maker, "block_c")

    section_a = mesh_maker.assembler.create_section(meshparts=["block_a"], num_partitions=1, merge_points=False)
    section_b = mesh_maker.assembler.create_section(meshparts=["block_b"], num_partitions=1, merge_points=False)
    section_c = mesh_maker.assembler.create_section(meshparts=["block_c"], num_partitions=1, merge_points=False)

    mesh_maker.assembler.remove(section_b.tag)

    assert list(mesh_maker.assembler.get_all()) == [1, 2]
    assert section_a.tag == 1
    assert section_c.tag == 2


def test_clear_empties_section_registry(mesh_maker):
    _make_brick_meshpart(mesh_maker, "block")
    mesh_maker.assembler.create_section(meshparts=["block"], num_partitions=1, merge_points=False)

    mesh_maker.assembler.clear()

    assert mesh_maker.assembler.get_all() == {}


def test_unregistered_assembly_section_has_no_tag(mesh_maker):
    _make_brick_meshpart(mesh_maker, "block")

    section = AssemblySection(
        meshpart_manager=mesh_maker.meshpart,
        meshparts=["block"],
        num_partitions=1,
        merge_points=False,
    )

    assert section._tag is None
    with pytest.raises(ValueError, match="has not been successfully created"):
        _ = section.tag
    assert mesh_maker.assembler.get_all() == {}


def test_assembler_runtime_state_is_instance_owned_not_class_shared():
    assembler_class_source = Path("src/femora/core/assembler.py").read_text(encoding="utf-8")
    assembler_class_body = assembler_class_source.split("class AssemblySection:", 1)[0]
    assembler_class_header = assembler_class_body.split("    def ", 1)[0]

    assert "_assembly_sections:" not in assembler_class_header
    assert "_instance = None" not in assembler_class_header
    assert "def __new__" not in assembler_class_header

    assert "_assembly_sections" not in CoreAssembler.__dict__
    assert "_instance" not in CoreAssembler.__dict__


def test_reset_clears_sections_and_assembled_mesh(mesh_maker):
    _make_brick_meshpart(mesh_maker, "block")
    mesh_maker.assembler.create_section(meshparts=["block"], num_partitions=1, merge_points=False)
    mesh_maker.assembler.assemble(merge_points=False)

    mesh_maker.assembler.reset()

    assert mesh_maker.assembled_mesh is None
    assert mesh_maker.assembler.get_all() == {}


def test_assembeled_actor_absent_from_core_assembler(mesh_maker):
    assert not hasattr(mesh_maker.assembler, "AssembeledActor")


def test_assembler_construction_is_not_singleton():
    assembler_a = CoreAssembler()
    assembler_b = CoreAssembler()

    assert assembler_a is not assembler_b
    assert assembler_a._assembly_sections is not assembler_b._assembly_sections


