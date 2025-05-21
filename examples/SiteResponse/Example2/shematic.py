# %% code for creating the shematic figure
import pyvista as pv
import h5py
import os 
import numpy as np

# Load the mesh
os.chdir(os.path.dirname(__file__))
filename = "Results/result0.vtkhdf"
mesh = pv.read(filename)

# Read displacement (not used here)
with h5py.File(filename, "r") as f:
    disp = f["VTKHDF"]["PointData"]["displacement"][()]
    dispoffset = f["VTKHDF"]["Steps"]["PointDataOffsets"]["displacement"][()]

# Tag material layers
cellcenters = mesh.cell_centers().points[:, 2]
materials = np.full(cellcenters.shape, 2, dtype=int)  # looseOttawa
materials[cellcenters < -2] = 3  # monteraySand
materials[cellcenters < -8] = 1  # denseOttawa
mesh["material"] = materials

# Create plotter and add mesh
plotter = pv.Plotter()
color_cycle = ["saddlebrown", "peru", "burlywood"]
plotter.add_mesh(mesh, show_edges=True, scalars="material", cmap=color_cycle, show_scalar_bar=False, opacity=1.0)

# Coordinates for dimension line and ticks
x_offset = mesh.center[0] + 0.7  # offset to the right of the mesh
tick_length = 0.2

# Define depths and labels
layer_tops = [0, -2, -8, -18]
midpoints = [-1, -5, -13]
labels = ["2 m", "6 m", "10 m"]

# Draw vertical dimension line
line_points = np.array([[x_offset, 0, z] for z in [layer_tops[0], layer_tops[-1]]])
plotter.add_lines(line_points, color="black", width=2)

# Draw horizontal ticks and add text
for z, label,z2 in zip(layer_tops, labels, midpoints):
    tick = np.array([
        [x_offset - tick_length/2, 0, z],
        [x_offset + tick_length/2, 0, z]
    ])
    plotter.add_lines(tick, color="black", width=4)
    plotter.add_point_labels(
        np.array([[x_offset + tick_length + 0.05, 0, z2]]),
        [label],
font_size=23, point_size=0, text_color='black',fill_shape=False,
                         shape_color="white",font_family="times"
    )
tick = np.array([
    [x_offset - tick_length/2, 0, -18],
    [x_offset + tick_length/2, 0, -18]
])
plotter.add_lines(tick, color="black", width=4)
# Finalize
plotter.view_xz()
plotter.show()
