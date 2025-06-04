# %%
import numpy as np
import h5py
import os
from femora.tools.transferFunction import TransferFunction, TimeHistory
import pyvista as pv
from pykdtree.kdtree import KDTree

os.chdir(os.path.dirname(__file__))
record = TimeHistory.load(acc_file="FrequencySweep.acc",
                            time_file="FrequencySweep.time",
                            unit_in_g=True,
                            gravity=9.81)

soil = [
    {"h": 2,  "vs": 144.2535646321813, "rho": 19.8*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
    {"h": 6,  "vs": 196.2675276462639, "rho": 19.1*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
    {"h": 10, "vs": 262.5199305117452, "rho": 19.9*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
]
rock = {"vs": 8000, "rho": 2000.0, "damping": 0.00}

# Create transfer function instance
tf = TransferFunction(soil, rock, f_max=50.0)

mesh = pv.read("mesh.vtk")
f, bh, acc, h, time, vel, disp, coords, internal = tf.createDRM(mesh, props={"shape":"box"}, time_history=record)
depth = -np.cumsum(np.append([0],h))  # Cumulative depth from the base

accx = acc.T
accy = np.zeros_like(accx)
accz = np.zeros_like(accx)
acc  = np.stack([accx, accy, accz], axis=1)
acc  = acc.reshape(-1, accx.shape[1])

velx = vel.T
vely = np.zeros_like(velx)
velz = np.zeros_like(velx)
vel  = np.stack([velx, vely, velz], axis=1)
vel  = vel.reshape(-1, velx.shape[1])

disp_x = disp.T
disp_y = np.zeros_like(disp_x)
disp_z = np.zeros_like(disp_x)
disp  = np.stack([disp_x, disp_y, disp_z], axis=1)
disp  = disp.reshape(-1, disp_x.shape[1])

dt = time[1] - time[0]

# find which index of the depth is each coordinate row
kdtree = KDTree(depth.reshape(-1, 1))
# Find the index of the closest depth for each coordinate
dist, data_location = kdtree.query(coords[:, 2].reshape(-1, 1), k=1)

if np.any(dist > 1e-5):
    raise ValueError(f"Some coordinates are not close to any depth in the DRM . Distances: {dist[dist > 1e-5]}")

data_location = data_location*3

zmin = np.min(coords[:, 2])
zmax = np.max(coords[:, 2])
xmin = np.min(coords[:, 0])
xmax = np.max(coords[:, 0])
ymin = np.min(coords[:, 1])
ymax = np.max(coords[:, 1])

dh = np.array([0,0,0])
drmbox_x0 = np.array([0,0,0])


file_name = "drmload.h5drm"
with h5py.File(file_name, "w") as f:
    # DRM_Data group
    drm_data = f.create_group("DRM_Data")
    # Create a dataset for coordinates
    # Path	/DRM_Data/xyz
    # Name	xyz
    # Type	Float, 64-bit, little-endian
    # Shape	? x 3 = 25854
    drm_data.create_dataset("xyz", data=coords, dtype='f8', shape=coords.shape)
    # /DRM_Data/internal
    # Name	internal
    # Type	Boolean
    # Shape	
    # Raw	
    # Inspect
    drm_data.create_dataset("internal", data=internal, dtype='b', shape=internal.shape)
    # Path	/DRM_Data/acceleration
    # Name	acceleration
    # Type	Float, 64-bit, little-endian
    # Shape	acc.shape[0] x acc.shape[1] = ?
    # Chunk shape	3 x acc.shape[1] = ?
    drm_data.create_dataset("acceleration", data=acc, dtype='f8', shape=acc.shape, chunks=(3, acc.shape[1]))
    # Path	/DRM_Data/velocity
    # Name	velocity
    # Type	Float, 64-bit, little-endian
    # Shape	vel.shape[0] x vel.shape[1] = ?
    # Chunk shape	3 x vel.shape[1] = ?
    drm_data.create_dataset("velocity", data=vel, dtype='f8', shape=vel.shape, chunks=(3, vel.shape[1]))
    # Path	/DRM_Data/displacement
    # Name	displacement
    # Type	Float, 64-bit, little-endian
    # Shape	disp.shape[0] x disp.shape[1] = ?
    # Chunk shape	3 x disp.shape[1] = ?
    drm_data.create_dataset("displacement", data=disp, dtype='f8', shape=disp.shape, chunks=(3, disp.shape[1]))
    # /DRM_Data/data_location
    # Name	data_location
    # Type	Integer (signed), 32-bit, little-endian
    # Shape	
    # Raw	
    # Inspect
    drm_data.create_dataset("data_location", data=data_location, dtype='i4', shape=data_location.shape)

    # /DRM_Metadata group
    drm_metadata = f.create_group("DRM_Metadata")
    # /DRM_Metadata/dt
    # Name	dt
    # Type	Float, 64-bit, little-endian
    # Shape	Scalar
    drm_metadata.create_dataset("dt", data=dt)
    # /DRM_Metadata/tend
    # Name	tend
    # Type	Float, 64-bit, little-endian
    # Shape	Scalar
    drm_metadata.create_dataset("tend", data=time[-1])

    # /DRM_Metadata/tstart
    # Name	tstart
    # Type	Float, 64-bit, little-endian
    # Shape	Scalar
    drm_metadata.create_dataset("tstart", data=time[0]  )
    # /DRM_Metadata/drmbox_zmin
    drm_metadata.create_dataset("drmbox_zmin", data=zmin  )
    # /DRM_Metadata/drmbox_zmax
    drm_metadata.create_dataset("drmbox_zmax", data=zmax  )
    # /DRM_Metadata/drmbox_xmin
    drm_metadata.create_dataset("drmbox_xmin", data=xmin  )
    # /DRM_Metadata/drmbox_xmax
    drm_metadata.create_dataset("drmbox_xmax", data=xmax  )
    # /DRM_Metadata/drmbox_ymin
    drm_metadata.create_dataset("drmbox_ymin", data=ymin  )
    # /DRM_Metadata/drmbox_ymax
    drm_metadata.create_dataset("drmbox_ymax", data=ymax  )

    # /DRM_Metadata/h
    # Name	h
    # Type	Float, 64-bit, little-endian
    # Shape	3
    # Raw	
    # Inspect
    drm_metadata.create_dataset("h", data=dh, dtype='f8', shape=(3,))

    # /DRM_Metadata/drmbox_x0
    # Name	drmbox_x0
    # Type	Float, 64-bit, little-endian
    # Shape	3
    # Raw	
    drm_metadata.create_dataset("drmbox_x0", data=drmbox_x0, dtype='f8', shape=(3,))


# %%
