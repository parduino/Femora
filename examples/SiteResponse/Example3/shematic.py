# %% code for creating the shematic figure
import pyvista as pv
import h5py
import os 
import numpy as np
from glob import glob

# Load the mesh
os.chdir(os.path.dirname(__file__))
filenames = sorted(glob("./Results/result*.vtkhdf"))  # Find all matching files

# Tag material layers
mesh = pv.MultiBlock()
for filename in filenames:
    mesh.append(pv.read(filename))
mesh = mesh.combine(merge_points=True)

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
x_offset = mesh.center[0] + 6  # offset to the right of the mesh
tick_length = 0.2

# Define depths and labels
layer_tops = [0, -2, -8, -18]
midpoints = [-1, -5, -13]
labels = ["2 m", "6 m", "10 m"]

# Draw vertical dimension line
line_points = np.array([[x_offset, x_offset, z] for z in [layer_tops[0], layer_tops[-1]]])
plotter.add_lines(line_points, color="red", width=5)

# Draw horizontal ticks and add text
for z, label, z2 in zip(layer_tops, labels, midpoints):
    tick = np.array([
        [x_offset - tick_length/2, x_offset - tick_length/2, z],
        [x_offset + tick_length/2, x_offset + tick_length/2, z]
    ])
    plotter.add_lines(tick, color="black", width=4)
    plotter.add_point_labels(
        np.array([[x_offset + tick_length + 0.05, x_offset + tick_length + 0.05, z2]]),
        [label],
        font_size=23, point_size=0, text_color='black', fill_shape=False,
        shape_color="white", font_family="times"
    )
tick = np.array([
    [x_offset - tick_length/2, x_offset - tick_length/2, -18],
    [x_offset + tick_length/2, x_offset - tick_length/2, -18]
])
plotter.add_lines(tick, color="black", width=5)

# Add width and length labels at the top
width_start = mesh.bounds[0]
width_end = mesh.bounds[1]
length_start = mesh.bounds[2]
length_end = mesh.bounds[3]

# Draw width dimension line
width_line = np.array([
    [width_start, length_end + 1, 0],
    [width_end, length_end + 1, 0]
])
plotter.add_lines(width_line, color="red", width=5)

# Add width label
plotter.add_point_labels(
    np.array([[(width_start + width_end) / 2, length_end + 1.2, 0]]),
    ["10 m"],
    font_size=23, point_size=0, text_color='black', fill_shape=False,
    shape_color="white", font_family="times"
)

# Draw length dimension line
length_line = np.array([
    [width_end + 1, length_start, 0],
    [width_end + 1, length_end, 0]
])
plotter.add_lines(length_line, color="red", width=5)

# Add length label
plotter.add_point_labels(
    np.array([[width_end + 1.2, (length_start + length_end) / 2, 0]]),
    ["10 m"],
    font_size=23, point_size=0, text_color='black', fill_shape=True,
    shape_color="white", font_family="times"
)

# Finalize
plotter.show_axes()
plotter.show()
