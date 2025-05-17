# %%
import pyvista as pv
import numpy as np
import h5py
import os
from tqdm import tqdm
from glob import glob
from itertools import cycle

os.chdir(os.path.dirname(__file__))
filenames = sorted(glob("./Results/result*.vtkhdf"))  # Find all matching files
stride = 20  # Skip frames to make it faster
pl = pv.Plotter()

pl.open_movie("movie.mp4", framerate=50)

# Preload all meshes and displacements
meshes = []
displacements = []
dispoffsets = []
points = []

for filename in tqdm(filenames, desc="Reading files"):
    mesh = pv.read(filename)
    meshes.append(mesh)
    points.append(mesh.points.copy())  # Store original points

    with h5py.File(filename, "r") as f:
        disp = f["VTKHDF"]["PointData"]["displacement"][()]
        dispoffset = f["VTKHDF"]["Steps"]["PointDataOffsets"]["displacement"][()]
        displacements.append(disp)
        dispoffsets.append(dispoffset)

for mesh in meshes:
    cellcenters = mesh.cell_centers().points[:, 2]
    materials = np.full(cellcenters.shape, 2, dtype=int)  # looseOttawa is 2
    materials[cellcenters < -2] = 3  # monteraySand is 3
    materials[cellcenters < -8] = 1  # denseOttawa is 1
    mesh["material"] = materials

color_cycle = ["saddlebrown", "peru", "burlywood"]

for mesh in meshes:
    pl.add_mesh(mesh, show_edges=True, opacity=1.0,scalars="material",clim=[1, 3], show_scalar_bar=False, cmap=color_cycle)
pl.open_movie("movie.mp4", framerate=50)
pl.write_frame()

# Update and render frames
for i in tqdm(range(len(dispoffsets[0]) // stride // 2), desc=f"Rendering frames"):
    for mesh, disp, dispoffset, point in zip(meshes, displacements, dispoffsets, points):
        ii = dispoffset[i * stride]
        jj = dispoffset[i * stride + 1]
        mesh.points = point + disp[ii:jj, :] * 15
    pl.write_frame()

pl.close()
