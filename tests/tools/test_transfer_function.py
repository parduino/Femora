# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

"""Tests for the public transfer-function workflow."""

import numpy as np

from femora.tools.transferFunction import TimeHistory, TransferFunction


def test_deconvolve_is_public_and_preserves_motion_metadata(monkeypatch):
    time = np.arange(0.0, 1.0, 0.01)
    acceleration = np.sin(2.0 * np.pi * 2.0 * time)
    motion = TimeHistory(
        time,
        acceleration,
        unit_in_g=False,
        metadata={"name": "surface"},
    )
    transfer_function = TransferFunction(
        soil_profile=[{"h": 1.0, "vs": 200.0, "rho": 1_800.0, "damping": 0.0}],
        rock={"vs": 800.0, "rho": 2_000.0, "damping": 0.0},
        f_max=1_000.0,
    )

    def constant_transfer_function(*, frequency, **_):
        values = np.full(frequency.shape, 2.0 + 0.0j)
        return frequency, values, values

    monkeypatch.setattr(transfer_function, "compute", constant_transfer_function)

    incident, aligned_surface, _ = transfer_function.deconvolve(
        motion,
        return_all=True,
    )

    assert isinstance(incident, TimeHistory)
    assert incident.unit_in_g is False
    assert incident.metadata["name"] == "surface"
    assert incident.metadata["operation"] == "deconvolution"
    np.testing.assert_allclose(
        incident.acceleration,
        0.5 * aligned_surface.acceleration,
        atol=1.0e-12,
    )


def test_private_deconvolution_alias_matches_public_method(monkeypatch):
    time = np.arange(0.0, 0.5, 0.01)
    motion = TimeHistory(time, np.sin(2.0 * np.pi * time))
    transfer_function = TransferFunction(
        soil_profile=[{"h": 1.0, "vs": 200.0, "rho": 1_800.0, "damping": 0.0}],
        rock={"vs": 800.0, "rho": 2_000.0, "damping": 0.0},
        f_max=20.0,
    )

    def identity_transfer_function(*, frequency, **_):
        values = np.ones(frequency.shape, dtype=complex)
        return frequency, values, values

    monkeypatch.setattr(transfer_function, "compute", identity_transfer_function)

    public = transfer_function.deconvolve(motion)
    private = transfer_function._deconvolve(motion)
    np.testing.assert_allclose(private.time, public.time)
    np.testing.assert_allclose(private.acceleration, public.acceleration)
