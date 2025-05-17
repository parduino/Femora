# %% 
import pyvista as pv
import h5py
import os 
from tqdm import tqdm

os.chdir(os.path.dirname(__file__))
filename = "Results/result0.vtkhdf"

mesh = pv.read(filename)

with h5py.File(filename, "r") as f:
    disp = f["VTKHDF"]["PointData"]["displacement"][()]
    dispoffset = f["VTKHDF"]["Steps"]["PointDataOffsets"]["displacement"][()]


# disp = disp.reshape(-1, 3, 104)
print(disp.shape)
# exit()
# now create a movie
stride = 20  # Skip frames to make it faster
points = mesh.points
pl = pv.Plotter()
pl.add_mesh(mesh, show_edges=True, color="royalblue", opacity=1.0)
pl.camera_position = "xz"
pl.open_movie("movie.mp4",framerate=50)
pl.write_frame()
for i in tqdm(range(len(dispoffset)//stride//2), desc="Rendering frames"):
    ii = dispoffset[i * stride]
    jj = dispoffset[i * stride + 1]
    mesh.points = points + disp[ii:jj,:] * 15
    pl.write_frame()
pl.close()

    
    

# %%
