import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import h5py
from matplotlib.ticker import AutoMinorLocator

# Set up matplotlib for publication quality
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.figsize': (10, 10),
    'figure.dpi': 300
})

# ============= USER CONFIGURATION =============
# Specify the folders to compare (you can modify this list)
folders_to_compare = ["Results_Fixed", "Results_PML", "Results_Rayleigh"]  # Change to ["Regular", "Vs150"] or any other folders as needed

# Colors and styles for each folder
folder_styles = {
    "Results_Fixed": {"color": "blue", "linestyle": "-", "linewidth": 1.5},
    "Results_PML": {"color": "red", "linestyle": "-", "linewidth": 1.5},
    "Results_Rayleigh": {"color": "green", "linestyle": "-", "linewidth": 1.5},
    # Add more folders with their styles as needed
}

# User-defined y-axis ranges for each component (min, max)
y_ranges = [
    (-0.02, 0.02),  # y-range for a_x
    (-0.02, 0.02),  # y-range for a_y
    (-0.02, 0.02)   # y-range for a_z
]

# Output filename (without extension)
output_filename = f"acceleration_comparison_{'_'.join(folders_to_compare)}"

# Maximum time to plot (seconds)
max_time = 25.0
# ============================================

# Change to the script's directory
os.chdir(os.path.dirname(__file__))


def process_vtk_data(folder, desired_point):
    """Process VTK HDF files in the specified folder for a given point."""
    basename = f"{folder}/result"
    files = sorted(glob.glob(f"{basename}*.vtkhdf"))
    for filename in files:
        try:
            with h5py.File(filename, "r") as f:
                points = f["VTKHDF"]["Points"][()]
                if points.size == 0:
                    continue
                distances = np.linalg.norm(points - desired_point, axis=1)
                closest_index = np.argmin(distances)
                closest_point = points[closest_index]
                if distances[closest_index] > 1e-3:
                    continue
                print(f"Processing {folder}:")
                print(f"  Closest point to {desired_point}: {closest_point}")
                print(f"  Index: {closest_index}, Distance: {distances[closest_index]}")
                print(f"  Filename: {filename}")
                disp = f["VTKHDF"]["PointData"]["displacement"][()]
                displace_offset = f["VTKHDF"]["Steps"]["PointDataOffsets"]["displacement"][()]
                displace_offset += closest_index
                disp = disp[displace_offset]
                print(f"  Displacement shape: {disp.shape}")
                time = f["VTKHDF"]["Steps"]["Values"][()]
                index = np.where(time < max_time)[0]
                time_filtered = time[index]
                disp_filtered = disp[index]
                return time_filtered, disp_filtered
        except Exception as e:
            print(f"Failed to process {filename}: {e}")
    return None, None

# Define the three points for each subplot
points_to_plot = [
    np.array([-2.5, 0., 3.]),
    np.array([0., 0., 3.]),
    np.array([2.5, 0., 3.])
]
point_labels = [
    'Point (-2.5, 0, 3)',
    'Point (0, 0, 3)',
    'Point (2.5, 0, 3)'
]

# Create figure with three subplots (one for each point)
fig, axs = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
fig.subplots_adjust(hspace=0.1)

# For each subplot (point), process and plot data from each folder
for i, (desired_point, label) in enumerate(zip(points_to_plot, point_labels)):
    for folder in folders_to_compare:
        print(f"\nProcessing {folder} for point {desired_point}...")
        time_data, disp_data = process_vtk_data(folder, desired_point)
        if time_data is None or disp_data is None:
            print(f"No valid data found in folder: {folder} for point {desired_point}")
            continue
        style = folder_styles.get(folder, {"color": "black", "linestyle": "-", "linewidth": 1.0})
        # Plot only the x-component (dx) of displacement
        dx = disp_data[:, 0]
        axs[i].plot(time_data, dx,
                    color=style["color"],
                    linestyle=style["linestyle"],
                    linewidth=style["linewidth"],
                    label=folder.split('_')[-1])
    axs[i].set_ylabel(f'{label}\ndx (m)')
    axs[i].grid(True, linestyle='--', alpha=0.7)
    axs[i].xaxis.set_minor_locator(AutoMinorLocator())
    axs[i].yaxis.set_minor_locator(AutoMinorLocator())
    axs[i].set_ylim(y_ranges[i])
    axs[i].legend(frameon=True, loc='upper right')

# Set common x-axis label
axs[2].set_xlabel('Time (s)')
fig.suptitle("Displacement Magnitude at Selected Points (Pile Head Time History)", fontsize=16)
plt.tight_layout()
plt.show()
# plt.savefig(f"{output_filename}.png", dpi=300, bbox_inches='tight')
# plt.savefig(f"{output_filename}.pdf", bbox_inches='tight')

