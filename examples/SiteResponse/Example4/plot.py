# %%
import numpy as np
import glob
import h5py
import os
import matplotlib.pyplot as plt
from femora.tools.transferFunction import TransferFunction

os.chdir(os.path.dirname(__file__))

# Maximum time to plot (seconds)
MAX_TIME = 40.0

def read_vtk_data(file_pattern, max_time,coord=[0., 0., 0.], res_type="acceleration"):
    """Read and process VTK HDF files."""
    files = sorted(glob.glob(file_pattern))
    print(f"Reading files: {files}")
    for filename in files:
        try:
            with h5py.File(filename, "r") as f:
                points = f["VTKHDF"]["Points"][()]
                if points.size == 0:
                    continue

                # Find the closest point to (0, 0, 0)
                distances = np.linalg.norm(points - np.array(coord), axis=1)
                closest_index = np.argmin(distances)
                if distances[closest_index] > 1e-3:
                    continue

                acc = f["VTKHDF"]["PointData"][res_type][()]
                accoffset = f["VTKHDF"]["Steps"]["PointDataOffsets"]["acceleration"][()]
                acc = acc[accoffset + closest_index]

                time = f["VTKHDF"]["Steps"]["Values"][()]
                index = np.where(time < max_time)[0]

                return time[index], acc[index]
        except Exception:
            continue
    return None, None

def compute_transfer_function(surface_time, surface_acc, bedrock_time, bedrock_acc, dt=None):
    """Compute the transfer function using FFT."""
    t_min, t_max = min(surface_time[0], bedrock_time[0]), max(surface_time[-1], bedrock_time[-1])
    dt = dt or min(np.mean(np.diff(surface_time)), np.mean(np.diff(bedrock_time)))
    common_time = np.arange(t_min, t_max, dt)

    surface_interp = np.interp(common_time, surface_time, surface_acc)
    bedrock_interp = np.interp(common_time, bedrock_time, bedrock_acc)
    surface_interp += bedrock_interp

    fft_surface = np.fft.rfft(surface_interp)
    fft_bedrock = np.fft.rfft(bedrock_interp)

    f = np.fft.rfftfreq(len(common_time), d=dt)
    TF = fft_surface / fft_bedrock
    return f, TF

def plot_acceleration(surface_time, surface_acc, bedrock_time, bedrock_acc, orignal_surface, orignal_surface_time,MAX_TIME=1.0):
    """Plot acceleration time history."""
    fig, axs = plt.subplots(3, 1, figsize=(10, 10), sharex=True, sharey=True)
    fig.subplots_adjust(hspace=0.1)
    labels = ['$a_x$', '$a_y$', '$a_z$']

    surface_correction = np.interp(surface_time, bedrock_time, bedrock_acc)
    surface_acc /= 9.81

    for i in range(3):
        axs[i].plot(surface_time, surface_acc[:, i] + (surface_correction if i == 0 else 0), label='Numerical Surface')
        axs[i].plot(bedrock_time, bedrock_acc if i == 0 else np.zeros_like(bedrock_time), label='Bedrock', color='red')
        axs[i].plot(orignal_surface_time, orignal_surface if i == 0 else np.zeros_like(orignal_surface_time), label='Analytical Surface', linestyle='--', color='green')
        axs[i].set_ylabel(labels[i])
        axs[i].legend(loc='upper right')
        axs[i].grid()
        axs[i].set_xlim([0, MAX_TIME])

    axs[2].set_xlabel('Time (s)')
    plt.suptitle('Acceleration Time History')
    plt.show()

def plot_transfer_function(f, TF_num, f_analytical, TF_analytical):
    """Plot transfer function."""
    plt.plot(f, np.abs(TF_num), "b-", label="Numerical")
    plt.plot(f_analytical, TF_analytical, "r--", label="Analytical")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("|TF(f)|")
    plt.legend()
    plt.grid(True)
    plt.show()

# Main execution
surface_time, surface_acc = read_vtk_data("./Results/result*.vtkhdf", MAX_TIME)
bedrock_time = np.loadtxt("ricker_base.time")
bedrock_acc = np.loadtxt("ricker_base.acc")
orignal_surface = np.loadtxt("ricker_surface.acc")
orignal_surface_time = np.loadtxt("ricker_surface.time")

if surface_time is not None and surface_acc is not None:
    plot_acceleration(surface_time, surface_acc, bedrock_time, bedrock_acc,orignal_surface, orignal_surface_time)

    f, TF_num = compute_transfer_function(surface_time, surface_acc[:, 0], bedrock_time, bedrock_acc)
    mask = (f < 30) & (f > 0)
    f, TF_num = f[mask], TF_num[mask]

    # New analytical transfer function calculation
    soil = [
        {"h": 2,  "vs": 144.2535646321813, "rho": 19.8*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
        {"h": 6,  "vs": 196.2675276462639, "rho": 19.1*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
        {"h": 10, "vs": 262.5199305117452, "rho": 19.9*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
    ]
    rock = {"vs": 8000, "rho": 2000.0, "damping": 0.00}
    tf = TransferFunction(soil_profile=soil, rock=rock, f_max=30)
    
    f_analytical, TF_analytical, _ = tf.compute()

    plot_transfer_function(f, TF_num, f_analytical, np.abs(TF_analytical))


else:
    print("No data found in the specified VTK files.")

# %%
