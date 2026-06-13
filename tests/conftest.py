# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--show-partitions",
        action="store_true",
        default=False,
        help="Show PyVista windows for partitioner tests (interactive).",
    )

    parser.addoption(
        "--time-partitions",
        action="store_true",
        default=False,
        help="Run/print partitioner timing benchmarks (can be slow).",
    )

    parser.addoption(
        "--partition-bench-k",
        action="store",
        type=int,
        default=16,
        help="Number of partitions to use for the timing benchmark.",
    )

    parser.addoption(
        "--partition-bench-repeat",
        action="store",
        type=int,
        default=1,
        help="Repeat each partitioner this many times and report best/median.",
    )

    parser.addoption(
        "--partition-bench-mesh",
        action="append",
        default=[],
        help="Mesh file path(s) to benchmark (VTK/VTU). Can be passed multiple times.",
    )


@pytest.fixture(scope="session")
def show_partitions(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--show-partitions"))


@pytest.fixture(scope="session")
def time_partitions(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--time-partitions"))


@pytest.fixture(scope="session")
def partition_bench_k(request: pytest.FixtureRequest) -> int:
    return int(request.config.getoption("--partition-bench-k"))


@pytest.fixture(scope="session")
def partition_bench_repeat(request: pytest.FixtureRequest) -> int:
    return int(request.config.getoption("--partition-bench-repeat"))


@pytest.fixture(scope="session")
def partition_bench_mesh(request: pytest.FixtureRequest) -> list[str]:
    value = request.config.getoption("--partition-bench-mesh")
    return [str(v) for v in (value or [])]
