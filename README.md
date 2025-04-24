# FEMORA - Fast Efficient Meshing for OpenSees-based Resilience Analysis

<div align="center">
  <img src="docs/images/Simcenter_Femora2.png" alt="FEMORA Logo" width="400"/>
  <br>
  <em>A powerful framework for finite element meshing and seismic analysis</em>
</div>

## Overview

FEMORA (Fast Efficient Meshing for OpenSees-based Resilience Analysis) is a Python-based framework designed to simplify the creation, management, and analysis of complex finite element models for seismic analysis. Built on top of OpenSees, FEMORA provides an intuitive API for mesh generation, material definition, and analysis configuration with a focus on soil dynamics and seismic simulations.

## Key Features

- **Powerful Mesh Generation**: Create complex 3D soil and structural models with minimal code
- **Domain Reduction Method (DRM)**: Advanced seismic analysis technique for realistic wave propagation
- **Material Library**: Comprehensive collection of soil and structural materials
- **Analysis Components**: Full suite of solvers, algorithms, integrators, and convergence tests
- **Visualization Tools**: Built-in visualization capabilities for model inspection and result analysis
- **OpenSees Integration**: Seamless export to OpenSees TCL files for simulation
- **GUI Support**: Optional graphical interface for model construction and visualization

## Installation

### Requirements

- Python 3.8 or higher
- OpenSees (for running exported models)

### Method 1: Using pip

```bash
pip install femora
```

### Method 2: From Source

```bash
git clone https://github.com/username/FEMORA.git
cd FEMORA
pip install -e .
```

### Method 3: Using conda

```bash
conda env create -f environment.yml
conda activate myenv
```

## Quick Start Example

```python
import femora as fm

# Initialize FEMORA
model = fm.MeshMaker()

# Define materials
soil = fm.material.create_elastic_isotropic("soil", E=2e8, nu=0.3, rho=2000)

# Define mesh dimensions and discretization
model.add_box_region((-50, -50, -30), (50, 50, 0), (10, 10, 6), material=soil)

# Define boundary conditions
model.fix_node_group("bottom", (0, 0, -30), (0, 0, 0), (1, 1, 1))
model.apply_absorbing_boundary("sides", exclude="top")

# Set up analysis
model.analysis.set_solver_algorithm("Newton")
model.analysis.set_integrator("Newmark", gamma=0.5, beta=0.25)
model.analysis.set_numberer("RCM")

# Create recorders
model.recorder.add_node_recorder("displacement", "nodes", ["disp"])
model.recorder.add_element_recorder("stress", "elements", ["stress"])

# Export to OpenSees
model.export_to_tcl("mesh.tcl")

# Launch the GUI for visualization
model.gui()
```

## Documentation

Comprehensive documentation is available at [femora.readthedocs.io](https://femora.readthedocs.io) including:

- [Getting Started Guide](https://femora.readthedocs.io/introduction/getting_started.html)
- [Installation Instructions](https://femora.readthedocs.io/introduction/installation.html)
- [Quick Start Tutorial](https://femora.readthedocs.io/introduction/quick_start.html)
- [Examples and Tutorials](https://femora.readthedocs.io/introduction/examples.html)
- [Technical Documentation](https://femora.readthedocs.io/technical/index.html)
- [Developer Guide](https://femora.readthedocs.io/developer/index.html)

## Examples

FEMORA includes several comprehensive examples:

1. **[3D Layered Soil Profile for Seismic Analysis](https://femora.readthedocs.io/introduction/example1.html)**
2. **[Multi-layer Soil Model with Absorbing Boundaries](https://femora.readthedocs.io/introduction/example2.html)**
3. **[Soil-Structure Interaction with Building on Multi-layered Soil](https://femora.readthedocs.io/introduction/example3.html)**

Example files are available in the `examples/` folder.

## Domain Reduction Method (DRM)

FEMORA provides a comprehensive implementation of the Domain Reduction Method for efficient seismic wave propagation analysis:

```python
# Create DRM pattern
drm_pattern = fm.create_drm_pattern("pattern_name", h5_file="input_motion.h5")

# Set up DRM-specific process
drm = fm.DRM()
drm.set_pattern(drm_pattern)
drm.createDefaultProcess(dT=0.01, finalTime=10.0)
```

## Contributing

Contributions are welcome! Please check out our [contribution guidelines](CONTRIBUTING.md) for details.

## Code Style

FEMORA follows these style guidelines:

- **Imports**: PEP 8 order (stdlib → third-party → local)
- **Classes**: PascalCase with descriptive names
- **Methods/Variables**: snake_case
- **Private attributes**: Leading underscore (_variable_name)
- **Type annotations**: For all function parameters and returns
- **Documentation**: Google-style docstrings for classes and methods
- **Error handling**: Explicit exceptions with descriptive messages

## License

This project is licensed under the [License Name] - see the LICENSE file for details.

## Citing FEMORA

If you use FEMORA in your research, please cite:

```bibtex
@software{femora2025,
  author = {Pakzad, Amin},
  title = {FEMORA: Fast Efficient Meshing for OpenSees-based Resilience Analysis},
  year = {2025},
  url = {https://github.com/username/FEMORA}
}
```

## Contact

For questions or support, please contact [email@example.com](mailto:email@example.com).