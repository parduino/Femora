"""
Compute 1‑D shear‑wave transfer functions for a layered soil column
using the classic Kramer (1996) frequency‑domain transfer‑matrix method.

This module implements the transfer matrix method for computing 1D seismic site response
in layered soil profiles. It calculates both the transfer function between the top and
base of the soil column (TF_uu) and the transfer function between the top and incident
wave (TF_inc).

* Inputs  :
    soil_profile = [ {h, vs, rho, damping}, … ]   # top ↧ bottom
    rock         = {vs, rho, damping}             # elastic half‑space
    f_max   (Hz) – highest frequency of interest   (default 20 Hz)
    n_freqs       – number of frequency points     (default 2000)
* Outputs :
    f        – 1‑D array of frequencies (Hz)
    TF_uu    – complex transfer function  u_top / u_base
    TF_inc   – complex transfer function  u_top / u_incident

Example:
    >>> soil_profile = [
    ...     {"h": 2.0, "vs": 200.0, "rho": 1500.0, "damping": 0.05},
    ...     {"h": 54.0, "vs": 400.0, "rho": 1500.0, "damping": 0.05}
    ... ]
    >>> rock = {"vs": 850.0, "rho": 1500.0, "damping": 0.05}
    >>> tf = TransferFunction(soil_profile, rock, f_max=25.0)
    >>> f, TF_uu, TF_inc = tf.compute()
"""
import numpy as np
from numpy.fft import fft, ifft, fftfreq
import matplotlib.pyplot as plt
from typing import List, Dict, Union, Optional, Tuple, Any
from pyvista import UnstructuredGrid, Cube
import os
import re
from tqdm import tqdm

class TimeHistory:
    """Class to store and process acceleration time history data."""
    def __init__(self, time: np.ndarray, acceleration: np.ndarray, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize time history data.

        Args:
            time (np.ndarray): Time array in seconds
            acceleration (np.ndarray): Acceleration array in g
            metadata (Optional[Dict]): Dictionary containing metadata about the time history
        """
        self.time = np.array(time)
        self.acceleration = np.array(acceleration)
        self.metadata = metadata or {}
        if len(time) != len(acceleration):
            raise ValueError("Time and acceleration arrays must have the same length")
        # dt is optional, only if time is uniform
        diffs = np.diff(time)
        if len(diffs) < 1:
            raise ValueError("Time array must have at least two points") 
        if np.allclose(diffs, diffs[0]):
            self.dt = diffs[0]
        else:
            self.dt = np.min(diffs)
            self.time = np.arange(time[0], time[-1]+1.0e-6, self.dt) 
            self.acceleration = np.interp(self.time, time, acceleration)
        

    @staticmethod
    def load(file_path: str = None, format: str = 'auto', time_file: str = None, acc_file: str = None, delimiter: str = ',', skiprows: int = 0) -> 'TimeHistory':
        """
        Load a time history from a single file (auto, peer, csv) or from two files (time and acceleration).
        Args:
            file_path (str): Path to the time history file (peer/csv)
            format (str): Format of the file ('peer', 'csv', 'auto').
            time_file (str): Path to file containing time values (for two-file mode)
            acc_file (str): Path to file containing acceleration values (for two-file mode)
            delimiter (str): Delimiter for text files (default ',')
            skiprows (int): Number of rows to skip (default 0)
        Returns:
            TimeHistory: Loaded time history object
        """
        if time_file and acc_file:
            time = np.loadtxt(time_file, delimiter=delimiter, skiprows=skiprows)
            acc = np.loadtxt(acc_file, delimiter=delimiter, skiprows=skiprows)
            return TimeHistory(time, acc, metadata={'source': 'separate_files', 'time_file': time_file, 'acc_file': acc_file})
        if file_path is None:
            raise ValueError("file_path must be provided if not loading from two files.")
        if format == 'auto':
            format = TimeHistory._detect_format(file_path)
        if format == 'peer':
            return TimeHistory._load_peer_format(file_path)
        elif format == 'csv':
            return TimeHistory._load_csv_format(file_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def _detect_format(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            return 'csv'
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    if 'NPTS' in line and 'DT' in line:
                        return 'peer'
        except Exception:
            pass
        raise ValueError("Could not detect file format")

    @staticmethod
    def _load_peer_format(file_path: str) -> 'TimeHistory':
        import re
        from datetime import datetime
        with open(file_path, 'r') as f:
            lines = f.readlines()
        npts, dt = None, None
        data_start = 0
        for i, line in enumerate(lines):
            if 'NPTS' in line and 'DT' in line:
                match = re.search(r'NPTS\s*=\s*(\d+),\s*DT\s*=\s*([0-9.Ee+-]+)', line)
                if match:
                    npts = int(match.group(1))
                    dt = float(match.group(2))
                    data_start = i + 1
                    break
        if npts is None or dt is None:
            raise ValueError("Could not find NPTS and DT in PEER file header.")
        acc = []
        for line in lines[data_start:]:
            acc.extend([float(x) for x in line.strip().split() if x])
        acc = np.array(acc)
        if len(acc) != npts:
            raise ValueError(f"Expected {npts} points, found {len(acc)}.")
        time = np.arange(0, npts * dt, dt)
        if len(time) > len(acc):
            time = time[:len(acc)]
        elif len(acc) > len(time):
            acc = acc[:len(time)]
        metadata = {
            'format': 'peer',
            'npts': int(npts),
            'dt': dt,
            'filename': os.path.basename(file_path),
            'loaded_at': datetime.now().isoformat()
        }
        return TimeHistory(time, acc, metadata)

    @staticmethod
    def _load_csv_format(file_path: str) -> 'TimeHistory':
        from datetime import datetime
        data = np.loadtxt(file_path, delimiter=',', skiprows=1)
        time = data[:, 0]
        acc = data[:, 1]
        dt = time[1] - time[0] if len(time) > 1 else None
        metadata = {
            'format': 'csv',
            'npts': len(time),
            'dt': dt,
            'filename': os.path.basename(file_path),
            'loaded_at': datetime.now().isoformat()
        }
        return TimeHistory(time, acc, metadata)

    @property
    def duration(self) -> float:
        """Get the duration of the time history in seconds."""
        return self.time[-1] - self.time[0]

    @property
    def npts(self) -> int:
        """Get the number of points in the time history."""
        return len(self.time)

    def get_spectrum(self, periods: Optional[np.ndarray] = None,
                    damping: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute the response spectrum for the time history.

        Args:
            periods (Optional[np.ndarray]): Array of periods to compute spectrum at
            damping (float): Damping ratio (default: 0.05)

        Returns:
            Tuple[np.ndarray, np.ndarray]: Periods and spectral accelerations
        """
        if periods is None:
            # Default periods: 0.01 to 10 seconds, 100 points
            periods = np.logspace(-2, 1, 100)

        # Compute Fourier transform
        n = len(self.acceleration)
        freq = np.fft.rfftfreq(n, self.dt)
        acc_fft = np.fft.rfft(self.acceleration)

        # Compute response spectrum
        sa = np.zeros_like(periods)
        for i, T in enumerate(periods):
            omega = 2 * np.pi / T
            h = damping
            beta = np.sqrt(1 - h**2)
            
            # Transfer function for SDOF system
            H = 1 / (1 - (freq/omega)**2 + 2j*h*(freq/omega))
            
            # Compute response
            resp_fft = H * acc_fft
            resp = np.fft.irfft(resp_fft, n)
            
            # Get maximum absolute response
            sa[i] = np.max(np.abs(resp))

        return periods, sa

class TransferFunction:
    _instance = None
    _initialized = False

    def __new__(cls, soil_profile: List[Dict] = None, rock: Dict = None, f_max: float = 20.0, n_freqs: int = 2000):
        """
        Create or return the singleton instance of TransferFunction.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        #  update the soil profile and rock properties
        cls._instance.update_soil_profile(soil_profile)
        cls._instance.update_rock(rock)
        cls._instance.computed = False
        cls._instance.f_max = f_max
        return cls._instance

    def __init__(self, soil_profile: List[Dict] = None, rock: Dict = None, f_max: float = 20.0, n_freqs: int = 2000):
        """
        Initialize the transfer function calculator.

        This constructor sets up the transfer function calculator with the given soil profile
        and rock properties. The transfer function is computed immediately upon initialization.
        Since this is a singleton, subsequent initializations with different parameters will
        update the existing instance.

        Args:
            soil_profile (List[Dict]): List of dictionaries containing soil layer properties.
                Each dictionary must contain:
                - h (float): Layer thickness in meters
                - vs (float): Shear wave velocity in m/s
                - rho (float): Mass density in kg/m³
                - damping (float, optional): Material damping ratio (default: 0.0)
            rock (Dict): Dictionary containing rock properties:
                - vs (float): Shear wave velocity in m/s
                - rho (float): Mass density in kg/m³
                - damping (float, optional): Material damping ratio (default: 0.0)
            f_max (float, optional): Highest frequency of interest in Hz. Defaults to 20.0.
            n_freqs (int, optional): Number of frequency points. Defaults to 2000.

        Raises:
            ValueError: If required properties are missing in soil_profile or rock
            TypeError: If input types are incorrect

        Example:
            >>> soil_profile = [
            ...     {"h": 2.0, "vs": 200.0, "rho": 1500.0, "damping": 0.05},
            ...     {"h": 54.0, "vs": 400.0, "rho": 1500.0, "damping": 0.05}
            ... ]
            >>> rock = {"vs": 850.0, "rho": 1500.0, "damping": 0.05}
            >>> tf = TransferFunction(soil_profile, rock, f_max=25.0)
        """
        # Only initialize once or if parameters are provided
        if soil_profile is not None and rock is not None:
            self.soil_profile = soil_profile
            self.rock = rock
            self.f_max = f_max
            self.n_freqs = n_freqs
            
            # Initialize results
            self.f = None
            self.TF_uu = None
            self.TF_inc = None
            
            self.computed = False


    @staticmethod 
    def _get_DRM_points(mesh: UnstructuredGrid,
                        props: Dict[str, Any]) -> np.ndarray:
        """
        Extract DRM points from a mesh.
        Args:
            mesh (UnstructuredGrid): The mesh from which to extract points.
            Props (Dict[str, Any]): Dictionary containing properties of the mesh.
                - 'shape': Shape of the mesh (e.g., 'box', 'cylinder')

        Returns:
            np.ndarray: Array of DRM points.
        """
        # Extract DRM points from the mesh
        if props['shape'] == 'box':
            # Extract points from a box mesh
            bounds = mesh.bounds
            eps = 1e-6
            bounds = tuple(np.array(bounds) + np.array([eps, -eps, eps, -eps, eps, 10]))
            normal = [0, 0, 1]
            origin = [0, 0, bounds[5]-eps]

            cube = Cube(bounds=bounds)
            cube = cube.clip(normal=normal, origin=origin)
            clipped = mesh.copy().clip_surface(cube, invert=False, crinkle=True)
            cellCenters = clipped.cell_centers(vertex=True)

            Coords = clipped.points
            xmin, xmax, ymin, ymax, zmin, zmax = cellCenters.bounds
            # print(f"Bounds: {xmin}, {xmax}, {ymin}, {ymax}, {zmin}, {zmax}")
            # print(clipped.bounds)
            # filter out points inside the bounds with a small tolerance

            mask =  (Coords[:, 0] > xmin) & (Coords[:, 0] < xmax) & \
                    (Coords[:, 1] > ymin) & (Coords[:, 1] < ymax) & \
                    (Coords[:, 2] > zmin) 


            Coords = Coords[~mask]

            # Correct vlalues
            bin_size = 1e-3
            Coords = np.round(Coords / bin_size) * bin_size
        else:
            raise ValueError("other shape not supported not implemented yet. Please use box shape for now. props['shape'] = 'box')")


        # organize the coordinates by z
        return Coords
    

    def _get_DRM_soil_profile(self, coords: np.ndarray):
        """
        Refine the soil profile based on the coordinates of the mesh.

        Args:
            coords (np.ndarray): Array of coordinates from the mesh.

        Returns:
            List[Dict]: Refined soil profile.
        """
        # Refine the soil profile based on the coordinates

        coords = coords[np.argsort(-coords[:, 2])]
        
        # Create a new soil profile based on the coordinates
        unique_z, indices = np.unique(coords[:, 2], return_inverse=True)
        unique_z = unique_z[::-1]  # Reverse order to match zmax to zmin
        indices = indices[::-1]  # Reverse order to match zmax to zmin
        # print(f"Unique z values: {unique_z}")
        # print(f"Indices: {indices}")
        # print(f"z values: {coords[:, 2]}")
        # print(f"z values: {unique_z[indices]}")


        # from the uniq z calcute h
        h = -np.diff(unique_z)  # negative because z is descending
        depth = np.cumsum(h)
        # add zero at the beginning of depth
        maxdepth = depth[-1]


        if np.abs(maxdepth - self.get_total_depth()) > 1e-2:
            raise ValueError(f"the length of the soil profile is not equal to the length of the mesh")
        

        # Create a depth array from soil profile
        ProfileDepth = []
        for i in range(len(self.soil_profile)):
            ProfileDepth.append(self.soil_profile[i]['h'])
        ProfileDepth = np.cumsum(ProfileDepth)
        
        # combine profiel depth with the depth
        ProfileDepth = np.array(ProfileDepth)
        combinedepth = np.concatenate((ProfileDepth, depth))
        combinedepth = np.unique(combinedepth)
        # now create the new soil profile
        new_soil_profile = []
        i = 0
        j = 0
        elev = 0
        for j,zz in enumerate(ProfileDepth):
            while zz > combinedepth[i]-1e-2:
                # print(f"zz: {zz}, depth[index]: {combinedepth[i]}, h:{combinedepth[i] - elev}")
                new_layer = self.soil_profile[j].copy()
                new_layer['h'] = float(combinedepth[i] - elev)
                new_soil_profile.append(new_layer)
                elev = combinedepth[i]
                i += 1
                if i >= len(combinedepth):
                    break
            

        return new_soil_profile
    
    def depth_tf(self, mesh: UnstructuredGrid, props: Dict[str, Any], base_time_history: TimeHistory = None, progress_bar: Optional[tqdm] = None) -> None:

        if progress_bar is None:
            progress_bar = tqdm(total=100, desc="Computing DRM", unit="%", leave=False)
        progress_bar.update(0)
        coords = self._get_DRM_points(mesh, props)
        progress_bar.update(5)
        newProfile = self._get_DRM_soil_profile(coords)
        progress_bar.update(5)
    
        # now compute transferfunction
        h = np.array([l["h"] for l in newProfile], dtype=float)
        vs = np.array([l["vs"] for l in newProfile], dtype=float)
        rho = np.array([l["rho"] for l in newProfile], dtype=float)
        damp = np.array([l.get("damping", 0.0) for l in newProfile], dtype=float)
        damptype = np.array([l.get("damping_type", "constant") for l in newProfile], dtype=str)
        F1 = np.array([l.get("f1", 1.0) for l in newProfile], dtype=float)
        F2 = np.array([l.get("f2", 10.0) for l in newProfile], dtype=float)


        omega1 = 2 * np.pi * F1
        omega2 = 2 * np.pi * F2
        A0 = 2 * damp * omega1 * omega2 / (omega1 + omega2)
        A1 = 2 * damp / (omega1 + omega2)

        vs_bed = self.rock["vs"]
        rho_bed = self.rock["rho"]
        damp_bed = self.rock.get("damping", 0.0)

        # Interface impedance ratios α_j (layer j / layer j+1)
        alpha = rho*vs / np.append(rho[1:], rho_bed) / np.append(vs[1:], vs_bed)

        # Frequency grid
        f = np.linspace(1e-6, self.f_max, self.n_freqs)  # avoid ω=0
        omega = 2*np.pi*f

        TF_uu = np.empty_like(f, dtype=complex)
        DRM_TFs = []
        
        for i in range(len(h)):
            # Loop over ω
            for k, w in enumerate(omega):
                # Total layer product L = Ln … L2 L1
                L = np.identity(2, dtype=complex)
                for j in range(i,len(h)):
                    if damptype[j].lower() == "constant":
                        damping = damp[j]
                    elif damptype[j].lower() == "rayleigh":
                        a0 = A0[j]
                        a1 = A1[j]
                        damping = a0 / (2 * w) + a1 * w / 2
                        
                    cj = np.sqrt(1 + 1j*damping*2)  # viscoelastic correction
                    rj = w * h[j] / vs[j] * cj
                    L = self._layer_matrix(alpha[j], rj) @ L
                    

                den = L[0,0] + L[0,1] + L[1,0] + L[1,1]  # u_top / u_base
                TF_uu[k] = 2.0 / den

            DRM_TFs.append(TF_uu.copy())
            # Update progress bar
            progress_bar.n = i * 30 // len(h)  + 10
            progress_bar.refresh()
        progress_bar.n = 40

        return f, DRM_TFs


        # dt = base_time_history.dt
        # acc = base_time_history.acceleration
        # n = len(acc)

        
        # # FFT of the base motion
        # acc_fft = fft(acc)
        # freqs = fftfreq(n, dt)

        # accelrations = []
        # for i,TF in enumerate(DRM_TFs):
        #     # Prepare transfer function
        #     TF_freq = f

        #     # Interpolate TF to match the fft frequencies
        #     TF_interp = np.interp(np.abs(freqs), TF_freq, TF, left=0, right=0)

        #     # Make the TF symmetric for inverse FFT (real time signal)
        #     TF_interp = TF_interp.astype(complex)

        #     # Apply TF to base motion in frequency domain
        #     surface_fft = acc_fft * TF_interp

        #     # Inverse FFT to get surface time history
        #     surface_motion = np.real(ifft(surface_fft))
        #     accelrations.append(surface_motion.copy())

        #     # update progress bar
        #     progress_bar.n = i * 30 // len(h) + 40
        #     progress_bar.refresh()
        

        # Z = np.cumsum(-h)
        # Z -= Z[0]
        # print(f"Z: {Z}")
        # return accelrations, Z, dt, n, DRM_TFs, f

        


        




    




        # progress_bar.n = 100
        # progress_bar.refresh()

        print(len(DRM_TFs))
            


            





    def compute_surface_motion(self, 
                               time_history:TimeHistory,
                               freqFlag:bool = False,
                               acc_fftFlag:bool = False,
                               surface_fftFlag:bool = False,
                               ) -> Dict[str, np.ndarray]:
        """
        Compute surface motion using the transfer function.

        Args:
            time_history (Optional[TimeHistory]): Input time history. If None,
                                                uses the last loaded time history.

        Returns:
            Tuple[np.ndarray, np.ndarray]: Time and surface acceleration arrays

        Raises:
            ValueError: If no time history is available
        """
        if time_history is None:
            raise ValueError("No time history available")
        
        if not self.computed:
            raise ValueError("Transfer function not computed yet")


        dt = time_history.dt
        acc = time_history.acceleration
        n = len(acc)
        
        # FFT of the base motion
        acc_fft = fft(acc)
        freqs = fftfreq(n, dt)

        # Prepare transfer function
        TF = self.TF_uu  # should be complex-valued, len = len(f)
        TF_freq = self.f  # positive frequency range of TF

        # Interpolate TF to match the fft frequencies
        TF_interp = np.interp(np.abs(freqs), TF_freq, TF, left=0, right=0)

        # Make the TF symmetric for inverse FFT (real time signal)
        TF_interp = TF_interp.astype(complex)

        # Apply TF to base motion in frequency domain
        surface_fft = acc_fft * TF_interp

        # Inverse FFT to get surface time history
        surface_motion = np.real(ifft(surface_fft))

        # Return desired outputs
        result = {
            "surface_acc": surface_motion,
        }

        index = np.where((freqs > 0) & (freqs < self.f_max))[0]
        freqs = freqs[index]
        acc_fft = acc_fft[index]
        surface_fft = surface_fft[index]

        if freqFlag:
            result["freq"] = freqs
        if acc_fftFlag:
            result["acc_fft"] = acc_fft
        if surface_fftFlag:
            result["surface_fft"] = surface_fft

        return result


    def plot_surface_motion(self, time_history: TimeHistory,
                          fig=None, **kwargs) -> 'matplotlib.figure.Figure':
        """
        Plot the surface motion.

        Args:
            time_history (TimeHistory): Input time history.
            fig (matplotlib.figure.Figure, optional): Existing figure to plot into.
                If None, a new figure will be created.
            **kwargs: Additional plotting parameters

        Returns:
            matplotlib.figure.Figure: The figure object containing the plot
        """
        import matplotlib.pyplot as plt

        if not self.computed:
            self.compute()
        
        time = time_history.time
        acc = time_history.acceleration

        res = self.compute_surface_motion(time_history,
                                          freqFlag=True,
                                          acc_fftFlag=True,
                                          surface_fftFlag=True)
        freq = res['freq']
        acc_fft = res['acc_fft']
        surface_fft = res['surface_fft']
        surface_acc = res['surface_acc']

        # Use provided figure or create a new one
        if fig is None:
            fig = plt.figure(figsize=(8, 11))
        
        # Clear any existing axes
        fig.clear()
        
        # Create 5 subplots
        axs = [fig.add_subplot(5, 1, i+1) for i in range(5)]
        axs.reverse()
        box = dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3')

        # 1. Time history
        axs[0].plot(time, acc)
        axs[0].set_title("Input Time History", loc="right", y=0.9, bbox=box)
        axs[0].set_xlabel("Time (s)")
        axs[0].set_ylabel("Acceleration (g)")

        # 2. Frequency content (FFT magnitude)
        axs[1].plot(freq, np.abs(acc_fft))
        axs[1].set_title("Frequency Content (|FFT|)", loc="right", y=0.9, bbox=box)
        axs[1].set_xlabel("Frequency (Hz)")
        axs[1].set_ylabel("|FFT|")

        # 3. Transfer function
        axs[2].plot(self.f, np.abs(self.TF_uu))
        axs[2].set_title("Transfer Function", loc="right", y=0.9, bbox=box)
        axs[2].set_xlabel("Frequency (Hz)")
        axs[2].set_ylabel("|TF|")

        # 4. Product in frequency domain
        axs[3].plot(freq, np.abs(surface_fft))
        axs[3].set_title("Product: |FFT(input) * TF|", loc="right", y=0.9, bbox=box)
        axs[3].set_xlabel("Frequency (Hz)")
        axs[3].set_ylabel("|Output FFT|")

        # 5. Inverse FFT (surface motion)
        axs[4].plot(time_history.time, surface_acc)
        axs[4].set_title("Surface Motion (Inverse FFT)", loc="right", y=0.9, bbox=box)
        axs[4].set_xlabel("Time (s)")
        axs[4].set_ylabel("Acceleration (g)")

        fig.tight_layout()
        return fig
        
    @staticmethod
    def _layer_matrix(alpha: float, r: float) -> np.ndarray:
        """
        Compute the layer matrix for a given impedance ratio and phase.

        This method computes the 2x2 transfer matrix for a single layer in the
        frequency domain, considering the impedance ratio and phase shift.

        Args:
            alpha (float): Impedance ratio between adjacent layers
            r (float): Phase shift parameter (ωh/vs)

        Returns:
            np.ndarray: 2x2 complex transfer matrix for the layer

        Note:
            The layer matrix is used in the transfer matrix method to propagate
            waves through the soil profile.
        """
        e_pos, e_neg = np.exp(1j * r), np.exp(-1j * r)
        return 0.5 * np.array([[ (1+alpha)*e_pos, (1-alpha)*e_neg],
                              [ (1-alpha)*e_pos, (1+alpha)*e_neg ]],
                             dtype=complex)

    def compute(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute the transfer functions for the soil profile.

        This method calculates both the transfer function between the top and base
        of the soil column (TF_uu) and the transfer function between the top and
        incident wave (TF_inc) using the transfer matrix method.

        Returns:
            Tuple[np.ndarray, np.ndarray, np.ndarray]: A tuple containing:
                - f: Array of frequencies in Hz
                - TF_uu: Complex transfer function u_top/u_base
                - TF_inc: Complex transfer function u_top/u_incident

        Note:
            The computation is performed in the frequency domain using the
            transfer matrix method. Results are stored in instance variables
            and also returned.
        """
        # Unpack layers
        h = np.array([l["h"] for l in self.soil_profile], dtype=float)
        vs = np.array([l["vs"] for l in self.soil_profile], dtype=float)
        rho = np.array([l["rho"] for l in self.soil_profile], dtype=float)
        damp = np.array([l.get("damping", 0.0) for l in self.soil_profile], dtype=float)
        damptype = np.array([l.get("damping_type", "constant") for l in self.soil_profile], dtype=str)
        F1 = np.array([l.get("f1", 1.0) for l in self.soil_profile], dtype=float)
        F2 = np.array([l.get("f2", 10.0) for l in self.soil_profile], dtype=float)
        omega1 = 2 * np.pi * F1
        omega2 = 2 * np.pi * F2
        A0 = 2 * damp * omega1 * omega2 / (omega1 + omega2)
        A1 = 2 * damp / (omega1 + omega2)

        vs_bed = self.rock["vs"]
        rho_bed = self.rock["rho"]
        damp_bed = self.rock.get("damping", 0.0)

        # Interface impedance ratios α_j (layer j / layer j+1)
        alpha = rho*vs / np.append(rho[1:], rho_bed) / np.append(vs[1:], vs_bed)

        # Frequency grid
        self.f = np.linspace(1e-6, self.f_max, self.n_freqs)  # avoid ω=0
        omega = 2*np.pi*self.f

        self.TF_uu = np.empty_like(self.f, dtype=complex)
        self.TF_inc = np.empty_like(self.f, dtype=complex)

        # Loop over ω
        for k, w in enumerate(omega):
            # Total layer product L = Ln … L2 L1
            L = np.identity(2, dtype=complex)
            for j in range(len(h)):
                if damptype[j].lower() == "constant":
                    damping = damp[j]
                elif damptype[j].lower() == "rayleigh":
                    a0 = A0[j]
                    a1 = A1[j]
                    damping = a0 / (2 * w) + a1 * w / 2
                    
                cj = np.sqrt(1 + 1j*damping*2)  # viscoelastic correction
                rj = w * h[j] / vs[j] * cj
                L = self._layer_matrix(alpha[j], rj) @ L

            den = L[0,0] + L[0,1] + L[1,0] + L[1,1]  # u_top / u_base
            self.TF_uu[k] = 2.0 / den
            den_inc = L[0,0] + L[0,1]  # u_top / S_inc
            self.TF_inc[k] = 1.0 / den_inc

        self.computed = True
        return self.f, self.TF_uu, self.TF_inc

    def plot(self, plot_type: str = 'uu', ax=None, **kwargs) -> 'matplotlib.figure.Figure':
        """
        Plot the transfer function.

        This method creates a plot of either the u_top/u_base transfer function
        or the u_top/u_incident transfer function.

        Args:
            plot_type (str, optional): Type of transfer function to plot:
                - 'uu': Plot u_top/u_base transfer function (default)
                - 'inc': Plot u_top/u_incident transfer function
            ax (matplotlib.axes.Axes, optional): Existing axes to plot into.
                If None, a new figure and axes will be created
            **kwargs: Additional plotting parameters passed to matplotlib.pyplot.plot

        Returns:
            matplotlib.figure.Figure: The figure object containing the plot

        Raises:
            ValueError: If plot_type is not 'uu' or 'inc'

        Example:
            >>> tf.plot(plot_type='uu', color='blue', linewidth=2)
            >>> plt.show()
        """
        if not self.computed:
            raise ValueError("Transfer function not computed yet")
        
        # Use provided axes if available, otherwise create a new figure and axes
        fig = None
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
        else:
            fig = ax.figure
            
        if plot_type == 'uu':
            ax.plot(self.f, np.abs(self.TF_uu), **kwargs)
            ax.set_ylabel("|TF(uu)|")
        elif plot_type == 'inc':
            ax.plot(self.f, np.abs(self.TF_inc), **kwargs)
            ax.set_ylabel("|TF(inc)|")
        else:
            raise ValueError("plot_type must be either 'uu' or 'inc'")
            
        ax.set_xlabel("Frequency [Hz]")
        ax.grid(True)
        return fig

    def plot_soil_profile(self, ax=None, **kwargs) -> 'matplotlib.figure.Figure':
        """
        Plot the soil profile.
        
        Args:
            ax (matplotlib.axes.Axes, optional): Existing axes to plot into.
                If None, a new figure and axes will be created
            **kwargs: Additional plotting parameters passed to matplotlib.pyplot
            
        Returns:
            matplotlib.figure.Figure: The figure object containing the plot
        """
        # Use provided axes if available, otherwise create a new figure and axes
        fig = None
        if ax is None:
            fig = plt.figure(figsize=(2, 8))
            ax = fig.add_subplot(111)
        else:
            fig = ax.figure
        
        # Calculate depths
        depths = np.cumsum([0] + [layer["h"] for layer in self.soil_profile])
        
        # Plot soil layers
        for i in range(len(depths)-1):
            ax.fill_between([0, 1], [depths[i], depths[i]], 
                           [depths[i+1], depths[i+1]], alpha=0.3)
            ax.plot([0, 1], [depths[i], depths[i]], 'k-')
            ax.plot([0, 1], [depths[i+1], depths[i+1]], 'k-')
        
        # Plot rock
        rockdepth = depths[-1] * 1.2
        ax.fill_between([0, 1], [depths[-1], depths[-1]], 
                        [rockdepth, rockdepth], alpha=0.3, color='gray',
                        hatch='//')
        ax.text(0.5, (depths[-1] + rockdepth) / 2, "∞", 
               ha='center', va='center', fontsize=12, color='black')
        
        ax.invert_yaxis()
        ax.set_ylim(top=0, bottom=rockdepth)
        ax.set_xlim(0, 1)
        ax.set_xticks([])  # Remove x-axis ticks
        ax.set_xticklabels([])  # Remove x-axis labels
        fig.tight_layout()
        
        return fig

    def add_layer(self, layer: Dict, position: Optional[int] = None) -> None:
        """
        Add a new soil layer to the profile.

        This method adds a new soil layer to the profile at the specified position
        and recomputes the transfer function.

        Args:
            layer (Dict): Dictionary containing layer properties:
                - h (float): Layer thickness in meters
                - vs (float): Shear wave velocity in m/s
                - rho (float): Mass density in kg/m³
                - damping (float, optional): Material damping ratio
            position (Optional[int]): Position to insert the layer (0-based).
                If None, adds to the bottom of the profile.

        Raises:
            ValueError: If required layer properties are missing
            IndexError: If position is out of range

        Example:
            >>> tf.add_layer({"h": 5.0, "vs": 300.0, "rho": 1500.0, "damping": 0.05})
            >>> tf.add_layer({"h": 3.0, "vs": 250.0, "rho": 1500.0}, position=0)
        """
        if position is None:
            self.soil_profile.append(layer)
        else:
            self.soil_profile.insert(position, layer)

    def remove_layer(self, position: int) -> None:
        """
        Remove a soil layer from the profile.

        This method removes a soil layer from the profile at the specified position
        and recomputes the transfer function.

        Args:
            position (int): Position of the layer to remove (0-based)

        Raises:
            IndexError: If position is out of range

        Example:
            >>> tf.remove_layer(0)  # Remove the top layer
        """
        if 0 <= position < len(self.soil_profile):
            # check if the length of the soil profile is greater than 1
            if len(self.soil_profile) == 1:
                raise ValueError("Cannot remove the last layer")
            self.soil_profile.pop(position)
        else:
            raise IndexError("Layer position out of range")

    def modify_layer(self, position: int, **properties) -> None:
        """
        Modify properties of an existing soil layer.

        This method updates the properties of a soil layer at the specified position
        and recomputes the transfer function.

        Args:
            position (int): Position of the layer to modify (0-based)
            **properties: Layer properties to update:
                - h (float): Layer thickness in meters
                - vs (float): Shear wave velocity in m/s
                - rho (float): Mass density in kg/m³
                - damping (float): Material damping ratio

        Raises:
            IndexError: If position is out of range

        Example:
            >>> tf.modify_layer(0, vs=250.0, damping=0.06)
            >>> tf.modify_layer(1, h=10.0, rho=1600.0)
        """
        if 0 <= position < len(self.soil_profile):
            properties = dict(properties)
            
            if not self._check_soil_profile([properties]):
                raise ValueError("Invalid layer properties")
            self.soil_profile[position].update(properties)
        else:
            raise IndexError("Layer position out of range")
        
    def update_soil_profile(self, soil_profile: List[Dict]) -> None:
        """
        Update the soil profile.
        """
        if not self._check_soil_profile(soil_profile):
            raise ValueError("Invalid soil profile")
        self.soil_profile = soil_profile
        self.computed = False

    def _check_soil_profile(self, soil_profile: List[Dict]) -> bool:
        """
        Check if the soil profile is valid.
        Args:
            soil_profile (List[Dict]): The soil profile to check.

        Returns:
            bool: True if the soil profile is valid, False otherwise.
        
        Raises:
            ValueError: If the soil profile is not valid.
        """
        if not isinstance(soil_profile, list):
            raise ValueError("soil_profile must be a list")
        if len(soil_profile) == 0:
            raise ValueError("soil_profile must not be empty")
        if not all(isinstance(layer, dict) for layer in soil_profile):
            raise ValueError("soil_profile must be a list of dictionaries")
        if not all(key in layer for layer in soil_profile for key in ["h", "vs", "rho", "damping"]):
            raise ValueError("soil_profile must contain the keys: h, vs, rho, damping")
        if not all(isinstance(layer["h"], (int, float)) and layer["h"] > 0 for layer in soil_profile):
            raise ValueError("all layer thicknesses must be positive numbers")
        if not all(isinstance(layer["vs"], (int, float)) and layer["vs"] > 0 for layer in soil_profile):
            raise ValueError("all shear wave velocities must be positive numbers")
        if not all(isinstance(layer["rho"], (int, float)) and layer["rho"] > 0 for layer in soil_profile):
            raise ValueError("all mass densities must be positive numbers")
        if not all(isinstance(layer["damping"], (int, float)) and 0 <= layer["damping"] <= 1 for layer in soil_profile):
            raise ValueError("all damping values must be between 0 and 1")
        return True

    def update_rock(self, rock: Dict) -> None:
        """
        Update the rock properties.
        """
        if not self._check_rock(rock):
            raise ValueError("Invalid rock properties")
        self.rock = rock
        self.computed = False

    def _check_rock(self, rock: Dict) -> bool:
        """
        Check if the rock properties are valid.
        """
        if not isinstance(rock, dict):
            raise ValueError("rock must be a dictionary")
        if not all(key in rock for key in ["vs", "rho", "damping"]):
            raise ValueError("rock must contain the keys: vs, rho, damping")
        if not all(isinstance(value, (int, float)) for value in rock.values()):
            raise ValueError("all rock values must be numbers")
        if rock["vs"] <= 0 or rock["rho"] <= 0:
            raise ValueError("rock vs and rho must be positive")
        if rock["damping"] < 0 or rock["damping"] > 1:
            raise ValueError("rock damping must be between 0 and 1")
        return True
    
    def update_frequency(self, f_max: float) -> None:
        """
        Update the maximum frequency of interest.

        Args:
            f_max (float): New maximum frequency in Hz

        Example:
            >>> tf.update_frequency(30.0)
        """
        if f_max <= 0:
            raise ValueError("f_max must be positive")
        self.f_max = f_max
        self.computed = False

    def get_total_depth(self) -> float:
        """
        Get the total depth of the soil profile.

        Returns:
            float: Total depth of the soil profile in meters

        Example:
            >>> depth = tf.get_total_depth()
            >>> print(f"Total depth: {depth:.2f} m")
        """
        return sum(layer["h"] for layer in self.soil_profile)

    def get_fundamental_frequency(self) -> float:
        """
        Estimate the fundamental frequency of the soil profile.

        This method estimates the fundamental frequency by finding the frequency
        at which the transfer function has its maximum amplification.

        Returns:
            float: Fundamental frequency in Hz

        Example:
            >>> f0 = tf.get_fundamental_frequency()
            >>> print(f"Fundamental frequency: {f0:.2f} Hz")
        """
        return self.f[np.argmax(np.abs(self.TF_uu))]

    def get_amplification_factor(self) -> float:
        """
        Get the maximum amplification factor.

        This method returns the maximum amplification factor from the transfer function,
        which represents the maximum ratio of surface to base motion.

        Returns:
            float: Maximum amplification factor

        Example:
            >>> max_amp = tf.get_amplification_factor()
            >>> print(f"Maximum amplification: {max_amp:.2f}")
        """
        return np.max(np.abs(self.TF_uu))

    def get_layer_properties(self, position: int) -> Dict:
        """
        Get properties of a specific layer.

        This method returns a copy of the properties of the layer at the specified position.

        Args:
            position (int): Position of the layer (0-based)

        Returns:
            Dict: Dictionary containing layer properties:
                - h (float): Layer thickness in meters
                - vs (float): Shear wave velocity in m/s
                - rho (float): Mass density in kg/m³
                - damping (float): Material damping ratio

        Raises:
            IndexError: If position is out of range

        Example:
            >>> props = tf.get_layer_properties(0)
            >>> print(f"Layer properties: {props}")
        """
        if 0 <= position < len(self.soil_profile):
            return self.soil_profile[position].copy()
        else:
            raise IndexError("Layer position out of range")

    def get_rock_properties(self) -> Dict:
        """
        Get properties of the rock layer.

        This method returns a copy of the properties of the underlying rock layer.

        Returns:
            Dict: Dictionary containing rock properties:
                - vs (float): Shear wave velocity in m/s
                - rho (float): Mass density in kg/m³
                - damping (float): Material damping ratio

        Example:
            >>> rock_props = tf.get_rock_properties()
            >>> print(f"Rock properties: {rock_props}")
        """
        return self.rock.copy()

    def get_profile_summary(self) -> Dict:
        """
        Get a comprehensive summary of the soil profile.

        This method returns a dictionary containing various properties and
        characteristics of the soil profile.

        Returns:
            Dict: Dictionary containing:
                - total_depth (float): Total depth of the soil profile in meters
                - num_layers (int): Number of soil layers
                - layer_thicknesses (List[float]): List of layer thicknesses
                - fundamental_frequency (float): Fundamental frequency in Hz
                - max_amplification (float): Maximum amplification factor

        Example:
            >>> summary = tf.get_profile_summary()
            >>> print(f"Profile summary: {summary}")
        """
        return {
            "total_depth": self.get_total_depth(),
            "num_layers": len(self.soil_profile),
            "layer_thicknesses": [layer["h"] for layer in self.soil_profile],
        }



# ------------------- example / quick test ------------------------------------
if __name__ == "__main__":
    import matplotlib.pyplot as plt 
    soil = [
        {"h": 2,  "vs": 144.2535646321813, "rho": 19.8*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
        {"h": 6,  "vs": 196.2675276462639, "rho": 19.1*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
        {"h": 10, "vs": 262.5199305117452, "rho": 19.9*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
    ]

    rock = {
        "vs": 850.0,
        "rho": 1500.0,
        "damping": 0.05,
    }

    # Create transfer function instance
    tf = TransferFunction(soil, rock, f_max=25.0)









    # # Example: load a PEER file
    record = TimeHistory.load(acc_file="/home/amnp95/Projects/Femora/examples/SiteResponse/Example1/FrequencySweep.acc",
                              time_file="/home/amnp95/Projects/Femora/examples/SiteResponse/Example1/FrequencySweep.time")

    # tf.compute()
    # tf.plot_soil_profile()

    # # Plot the transfer function
    # tf.plot()
    # tf.plot_surface_motion(record)

    # plt.show()

    import pyvista as pv
    import numpy as np

    x = np.linspace(-10, 10, 100)
    y = np.linspace(-15, 15, 50)
    z = np.linspace(-18, 0, 30)

    x, y, z = np.meshgrid(x, y, z, indexing='ij')

    mesh = pv.StructuredGrid(x, y, z)
    mesh = pv.UnstructuredGrid(mesh)


    accelrations, Z, dt, n = tf._compute_DRM(mesh, {"shape": "box", "normal": "z"}, base_time_history=record)
    import matplotlib.pyplot as plt
    # Plot the results
    index = 0
    time = np.arange(0, n*dt, dt)
    acc = accelrations[index]

    plt.figure(figsize=(10, 5))
    plt.plot(time, acc)
    plt.title(f"Surface Motion for Layer {index+1}")
    plt.xlabel("Time (s)")  
    plt.ylabel("Acceleration (g)")
    plt.grid()
    plt.show()

    # pl = pv.Plotter()
    # pl.add_mesh(mesh, show_edges=True)
    # pl.add_mesh(pv.PolyData(coords), color='red', point_size=5, render_points_as_spheres=True)
    # pl.show()



