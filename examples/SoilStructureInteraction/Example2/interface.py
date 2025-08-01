import pyvista as pv
import numpy as np
import os
import h5py

# ----------------------------------------------------------------------------
# Helper to write a minimal PolyData VTKHDF file with transient displacement
# ---------------------------------------------------------------------------


def write_vtkhdf_polydata(points: np.ndarray,
                          time: np.ndarray,
                          disp: np.ndarray,
                          filename: str) -> None:
    """Write *points* and their transient displacement *disp* to *filename*.

    Parameters
    ----------
    points
        (n_points, 3) array with node coordinates.
    time
        (n_steps,) array with the simulation time of every step.
    disp
        (n_steps, n_points, 3) array with displacement vectors for every
        node and time step.
    filename
        Target *.vtkhdf* file. Will be overwritten.
    """

    # Basic sizes
    n_points = points.shape[0]
    n_steps = time.shape[0]

    # Flatten displacement so it can be stored in a single 2-D dataset
    disp_flat = disp.reshape(n_steps * n_points, 3).astype(np.float32)

    # ---- index dtype (VTK convention) ----
    idx_dtype = np.int32  # match working file

    # Pre-compute offsets required by the `Steps` group
    point_offsets = np.zeros(n_steps, dtype=idx_dtype)  # geometry is static
    part_offsets = np.zeros(n_steps, dtype=idx_dtype)   # one part per step
    n_parts = np.ones(n_steps, dtype=idx_dtype)

    # PointData offset: start index of each time slice in the flattened array
    pd_offsets = np.arange(0, n_steps * n_points, n_points, dtype=idx_dtype)

    with h5py.File(filename, "w") as f:
        root = f.create_group("VTKHDF")

        # ----- Metadata -----
        root.attrs["Version"] = (2, 3)
        root.attrs.create("Type", b"UnstructuredGrid", dtype=h5py.string_dtype("ascii"))

        # ---------------- Geometry (static in time) ----------------
        root.create_dataset("NumberOfPoints", data=np.array([n_points], dtype=idx_dtype))
        root.create_dataset("Points", data=points.astype(np.float64))

        # ---------------- Topology as VTK_VERTEX cells ----------------
        connectivity = np.arange(n_points, dtype=idx_dtype)
        offsets = np.arange(0, n_points + 1, dtype=idx_dtype)  # length = cells+1
        types_arr = np.ones(n_points, dtype=np.uint8)  # 1 = VTK_VERTEX

        root.create_dataset("Connectivity", data=connectivity)
        root.create_dataset("Offsets", data=offsets)
        root.create_dataset("Types", data=types_arr)

        # per-part summary datasets (shape (1,))
        root.create_dataset("NumberOfCells", data=np.array([n_points], dtype=idx_dtype))
        root.create_dataset("NumberOfConnectivityIds", data=np.array([connectivity.size], dtype=idx_dtype))

        # PointData – store every vector for every step in a single dataset
        pd = root.create_group("PointData")
        pd.create_dataset("Displacement", data=disp_flat.astype(np.float64), maxshape=(None, 3))

        # Temporal metadata
        steps = root.create_group("Steps")
        steps.attrs["NSteps"] = n_steps
        steps.create_dataset("Values", data=time.astype(np.float32))
        steps.create_dataset("PartOffsets", data=part_offsets)
        steps.create_dataset("NumberOfParts", data=n_parts)
        steps.create_dataset("PointOffsets", data=point_offsets)

        # Cell-related offsets – zero since we have no topological cells
        zeros1 = np.zeros((n_steps, 1), dtype=idx_dtype)
        steps.create_dataset("CellOffsets", data=zeros1)
        steps.create_dataset("ConnectivityIdOffsets", data=zeros1)

        # PointData offsets
        pdo = steps.create_group("PointDataOffsets")
        pdo.create_dataset("Displacement", data=pd_offsets)

    print(f"Wrote VTKHDF file: {filename}")

interfaces = pv.MultiBlock()
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)
files = os.listdir("./Results_Fixed")
path = "./Results_Fixed"
for filename in files:
    if filename.startswith("EmbeddedBeamSolidInterface_"):
        fname = os.path.join(path, filename)
        points = np.loadtxt(fname, 
                            delimiter="\t",
                            usecols=(1, 2, 3))
        interfaces.append(pv.wrap(points).delaunay_3d().extract_surface())
        print("fname:", filename)
        interface_name = filename.split("EmbeddedBeamSolidInterface")[1].split(".")[0]
        print("interface_name:", interface_name)
        disp_file = os.path.join(path, f"EmbeddedBeamSolid{interface_name}_displacement.out")
        if os.path.exists(disp_file):
            disp = np.loadtxt(disp_file, delimiter=" ")
            time,disp = disp[:, 0], disp[:, 1:]
            assert disp.shape[1] / 3 == points.shape[0], "Displacement data does not match points"

            # Reshape displacement to (n_steps, n_points, 3)
            disp = disp.reshape(disp.shape[0], points.shape[0], 3)

            # Write the interface data to VTKHDF
            out_name = os.path.join(path, f"{interface_name}.vtkhdf")
            write_vtkhdf_polydata(points, time, disp, out_name)

interfaces.plot(show_edges=True)







