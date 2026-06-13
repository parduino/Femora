# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

import pytest

from femora.core.model import Model


@pytest.fixture
def mesh_maker():
    mk = Model()
    mk.clear_model()
    return mk


def test_material_manager_has_no_get_material_alias(mesh_maker):
    assert not hasattr(mesh_maker.material, "get_material")
