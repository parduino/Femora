import numpy as np
import pytest
import pyvista as pv

import time
from pathlib import Path

from femora.components.partitioner import PartitionerRegistry


def _make_smoke_mesh() -> pv.UnstructuredGrid:
    """Small deterministic mesh for unit tests (keeps pytest fast)."""
    x = np.arange(0, 100, 2, dtype=float)
    y = np.arange(0, 100, 2, dtype=float)
    z = np.arange(0, 100, 2, dtype=float)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    grid = pv.StructuredGrid(X, Y, Z)
    return grid.cast_to_unstructured_grid()


def _make_test_mesh() -> pv.UnstructuredGrid:
    """Create a (potentially large) mesh for local timing/inspection.

    Note: unit tests use `_make_smoke_mesh()` to stay fast; `_make_test_mesh()`
    is used only for the opt-in timing benchmark.
    """
    x = np.arange(0, 100, 1, dtype=float)
    y = np.arange(0, 100, 1, dtype=float)
    z = np.arange(0, 100, 1, dtype=float)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    grid = pv.StructuredGrid(X, Y, Z)
    return grid.cast_to_unstructured_grid()



@pytest.mark.parametrize("method", ["kd-tree", "morton", "hilbert", "geometric"])
def test_partitioners_smoke(method: str):
    mesh = _make_smoke_mesh()
    k = 5

    labels = PartitionerRegistry.partition(mesh, k, partitioner=method)

    assert isinstance(labels, np.ndarray)
    assert labels.shape == (mesh.n_cells,)
    assert labels.dtype.kind in {"i", "u"}
    assert labels.min() >= 0
    assert labels.max() < k

    # Not all partitioners guarantee using all partitions for pathological meshes.
    # Also, if the test mesh has <2 cells, it cannot exercise multiple partitions.
    expected_min_partitions = 1 if (k <= 1 or mesh.n_cells < 2) else 2
    assert np.unique(labels).size >= expected_min_partitions


def _cut_faces_count(mesh: pv.UnstructuredGrid, labels: np.ndarray) -> int:
    """Count inter-partition faces using VTK cell-face adjacency.

    This is meant for comparison/inspection, not as a universal quality metric.
    """
    cuts = 0
    n_cells = int(mesh.n_cells)
    for cell_id in range(n_cells):
        for neigh in mesh.cell_neighbors(cell_id, connections="faces"):
            neigh = int(neigh)
            if neigh <= cell_id:
                continue
            cuts += int(labels[cell_id] != labels[neigh])
    return int(cuts)


def test_partitioners_show_differences(capsys, show_partitions: bool):
    """Demonstrate that different methods produce different assignments.

    Run with `pytest -s tests/partitioner/test_partitioners.py` to see the printed summary.
    Add `--show-partitions` to open an interactive PyVista window.
    """
    mesh = _make_smoke_mesh()
    k = 7

    results = {}
    for method in ["morton", "hilbert", "geometric", "kd-tree"]:
        results[method] = PartitionerRegistry.partition(mesh, k, partitioner=method)

    # Hilbert and Morton are different curves; on this mesh, assignments should differ.
    morton = results["morton"]
    hilbert = results["hilbert"]
    diff_fraction = float(np.mean(morton != hilbert))
    # Only enforce a "they differ" assertion when the test mesh is large enough
    # to make this meaningful.
    if mesh.n_cells >= 100:
        assert diff_fraction > 0.01  # expect at least 1% of cells assigned differently

    # Print simple comparison stats (visible with -s)
    for method, labels in results.items():
        counts = np.bincount(labels, minlength=k)
        cuts = _cut_faces_count(mesh, labels)
        print(f"{method}: counts={counts.tolist()} cut_faces={cuts}")

    if show_partitions:
        # Interactive visualization: 2x2 grid of the same mesh colored by Core.
        plotter = pv.Plotter(shape=(2, 2))
        methods = ["kd-tree", "morton", "hilbert", "geometric"]
        for idx, method in enumerate(methods):
            r, c = divmod(idx, 2)
            plotter.subplot(r, c)
            m = mesh.copy()
            m.cell_data["Core"] = results[method]
            plotter.add_text(method, font_size=12)
            plotter.add_mesh(m, scalars="Core", show_edges=True)
            plotter.view_isometric()
        plotter.link_views()
        plotter.show()

    out = capsys.readouterr().out
    # Ensure we printed something useful
    assert "morton:" in out and "hilbert:" in out


def test_partitioner_metis_smoke(show_partitions: bool):
    pytest.importorskip("pymetis")

    # mesh = _make_smoke_mesh()
    mesh = _make_test_mesh()
    k = min(5, max(1, int(mesh.n_cells)))

    labels = PartitionerRegistry.partition(mesh, k, partitioner="metis")

    assert isinstance(labels, np.ndarray)
    assert labels.shape == (mesh.n_cells,)
    assert labels.dtype.kind in {"i", "u"}
    assert labels.min() >= 0
    assert labels.max() < k
    expected_min_partitions = 1 if (k <= 1 or mesh.n_cells < 2) else 2
    assert np.unique(labels).size >= expected_min_partitions

    if show_partitions:
        plotter = pv.Plotter()
        m = mesh.copy()
        m.cell_data["Core"] = labels
        plotter.add_text("metis", font_size=12)
        plotter.add_mesh(m, scalars="Core", show_edges=True)
        plotter.view_isometric()
        plotter.show()


@pytest.mark.parametrize("method", ["kd-tree", "morton", "hilbert", "geometric"])
def test_show_partitioner(method: str, show_partitions: bool):
        """Interactive visualization for a single partitioner.

        This exists so commands like:
            pytest -q tests/partitioner/test_partitioners.py --show-partitions -k morton
        will actually open a PyVista window.
        """
        if not show_partitions:
                pytest.skip("Pass --show-partitions to enable visualization")

        mesh = _make_smoke_mesh()
        k = 7
        labels = PartitionerRegistry.partition(mesh, k, partitioner=method)

        plotter = pv.Plotter()
        m = mesh.copy()
        m.cell_data["Core"] = labels
        plotter.add_text(method, font_size=12)
        plotter.add_mesh(m, scalars="Core", show_edges=True)
        plotter.view_isometric()
        plotter.show()


def test_partitioners_timing(
    time_partitions: bool,
    partition_bench_k: int,
    partition_bench_repeat: int,
    partition_bench_mesh: list[str],
):
    """Opt-in benchmark that prints partitioner timings.

    Enable with:
      pytest -q -s tests/partitioner/test_partitioners.py --time-partitions -k timing

    Optionally benchmark real meshes:
      pytest -q -s tests/partitioner/test_partitioners.py --time-partitions -k timing \
        --partition-bench-mesh mesh.vtk --partition-bench-mesh soil_volumetric_mesh.vtk
    """
    if not time_partitions:
        pytest.skip("Pass --time-partitions to enable timing benchmarks")

    repeat = max(1, int(partition_bench_repeat))
    methods = ["kd-tree", "morton", "hilbert", "geometric", "metis"]

    meshes: list[tuple[str, pv.UnstructuredGrid]] = []
    if partition_bench_mesh:
        for mesh_path in partition_bench_mesh:
            p = Path(mesh_path)
            if not p.exists():
                pytest.skip(f"Benchmark mesh not found: {mesh_path}")
            meshes.append((str(p), pv.read(str(p)).cast_to_unstructured_grid()))
    else:
        meshes.append(("generated", _make_test_mesh()))

    for mesh_name, mesh in meshes:
        k = int(partition_bench_k)
        k = max(1, min(k, int(mesh.n_cells)))

        print("\n" + "=" * 72)
        print(f"Partitioner timing mesh='{mesh_name}' cells={mesh.n_cells} points={mesh.n_points} k={k} repeat={repeat}")
        print("(Run with -s to see this output)")

        for method in methods:
            try:
                PartitionerRegistry.validate(method)
            except ImportError as e:
                print(f"{method:10s}  unavailable  ({e})")
                continue
            except ValueError as e:
                print(f"{method:10s}  not-registered ({e})")
                continue

            times: list[float] = []
            for _ in range(repeat):
                t0 = time.perf_counter()
                labels = PartitionerRegistry.partition(mesh, k, partitioner=method)
                t1 = time.perf_counter()

                # Basic sanity check so timing can't silently skip work.
                assert labels.shape == (mesh.n_cells,)
                times.append(t1 - t0)

            best = float(min(times))
            median = float(np.median(times))
            mcells_per_s = (float(mesh.n_cells) / best / 1e6) if best > 0 else float("inf")
            print(f"{method:10s}  best={best:8.3f}s  median={median:8.3f}s  throughput={mcells_per_s:6.2f} Mcells/s")
