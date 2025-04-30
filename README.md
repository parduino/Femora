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

- Python 3.9 or higher

### Using Virtual Environments (Recommended)

It's recommended to install FEMORA in a virtual environment to avoid conflicts with other Python packages:

```bash
# Create a virtual environment
python -m venv femora-env

# Activate the virtual environment
# On Windows
femora-env\Scripts\activate
# On Unix or MacOS
source femora-env/bin/activate
```

### Method 1: Using pip

```bash
# Basic installation
pip install femora

# With GUI support
pip install femora[gui]

# Full installation with all dependencies
pip install femora[all]
```

### Method 2: From Source

```bash
git clone https://github.com/amnp95/Femora.git
cd Femora
pip install -e .          # Basic installation
pip install -e ".[gui]"   # With GUI support
pip install -e ".[all]"   # Full installation with all dependencies
```

## Documentation

Comprehensive documentation is available at [amnp95.github.io/Femora](https://amnp95.github.io/Femora) including:

- [Getting Started Guide](https://amnp95.github.io/Femora/introduction/getting_started.html)
- [Installation Instructions](https://amnp95.github.io/Femora/introduction/installation.html)
- [Quick Start Tutorial](https://amnp95.github.io/Femora/introduction/quick_start.html)
- [Examples and Tutorials](https://amnp95.github.io/Femora/introduction/examples.html)
- [Technical Documentation](https://amnp95.github.io/Femora/technical/index.html)
- [Developer Guide](https://amnp95.github.io/Femora/developer/index.html)

## Examples

FEMORA includes several comprehensive examples:

1. **[3D Layered Soil Profile for Seismic Analysis](https://amnp95.github.io/Femora/introduction/example1.html)**
2. **[Multi-layer Soil Model with Absorbing Boundaries](https://amnp95.github.io/Femora/introduction/example2.html)**

Example files are available in the `examples/` folder.

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
  author = {Pakzad, Amin and Arduino, Pedro},
  title = {FEMORA: Fast Efficient Meshing for OpenSees-based Resilience Analysis},
  year = {2025},
  url = {https://github.com/amnp95/Femora}
}
```

## Contact

For questions or support, please contact [email@example.com](mailto:email@example.com).