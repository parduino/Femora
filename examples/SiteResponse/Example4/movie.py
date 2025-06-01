# %% 
import pyvista as pv
import h5py
import os 
import numpy as np
from tqdm import tqdm


# Load the mesh
os.chdir(os.path.dirname(__file__))
filename = "Results/result0.vtkhdf"
mesh = pv.read(filename)

# Read displacement (not used here)
with h5py.File(filename, "r") as f:
    disp = f["VTKHDF"]["PointData"]["displacement"][()]
    dispoffset = f["VTKHDF"]["Steps"]["PointDataOffsets"]["displacement"][()]

# disp = disp[:,:1000]
# dispoffset = dispoffset[:,:1000]

# Tag material layers
cellcenters = mesh.cell_centers().points[:, 2]
materials = np.full(cellcenters.shape, 2, dtype=int)  # looseOttawa
materials[cellcenters < -2] = 3  # monteraySand
materials[cellcenters < -8] = 1  # denseOttawa
mesh["material"] = materials
# Create plotter and add mesh
color_cycle = ["saddlebrown", "peru", "burlywood"]

# now create a movie
stride =  20 # Skip frames to make it faster
points = mesh.points
pl = pv.Plotter()
pl.add_mesh(mesh, show_edges=True, color="royalblue", opacity=1.0, 
            scalars="material", cmap=color_cycle, show_scalar_bar=False)
pl.show_axes()
pl.open_movie("movie.mp4",framerate=50)
pl.write_frame()
time = 0 
dt = 0.001
for i in tqdm(range(len(dispoffset)//stride//2), desc="Rendering frames"):
    time = i * stride * dt
    if time > 1.0:
        break

    ii = dispoffset[i * stride]
    jj = dispoffset[i * stride + 1]
    mesh.points = points + disp[ii:jj,:] * 100
    pl.write_frame()
pl.close()

    
    

# %%
