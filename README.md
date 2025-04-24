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
git clone https://github.com/username/Femora.git
cd Femora
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

# defining the materials
fm.material.create_material(material_category="nDMaterial", material_type="ElasticIsotropic", user_name="Dense Ottawa", E=2.0e7, nu=0.3, rho=2.02)
fm.material.create_material(material_category="nDMaterial", material_type="ElasticIsotropic", user_name="Loose Ottawa", E=2.0e7, nu=0.3, rho=1.94)
fm.material.create_material(material_category="nDMaterial", material_type="ElasticIsotropic", user_name="Dense Montrey", E=2.0e7, nu=0.3, rho=2.018)

DensOttawaEle = fm.element.create_element(element_type="stdBrick", ndof=3, material="Dense Ottawa", b1=0.0, b2=0.0, b3=-9.81 * 2.02)
LooseOttawaEle = fm.element.create_element(element_type="stdBrick", ndof=3, material="Loose Ottawa", b1=0.0, b2=0.0, b3=-9.81 * 1.94)
MontreyEle = fm.element.create_element(element_type="stdBrick", ndof=3, material="Dense Montrey", b1=0.0, b2=0.0, b3=-9.81 * 2.018)

# defining the mesh parts
Xmin = -10.0
Xmax = 10.
Ymin = -10.0
Ymax = 10.
Zmin = -18.0
thick1 = 2.6
thick2 = 2.4
thick3 = 5.0 
thick4 = 6.0
thick5 = 2.0
dx = 1.0
dy = 1.0
dz1 = 1.3
dz2 = 1.2
dz3 = 1.0
dz4 = 0.5
dz5 = 0.5
Nx = int((Xmax - Xmin)/dx)
Ny = int((Ymax - Ymin)/dy)

fm.meshPart.create_mesh_part(category="Volume mesh",
                             mesh_part_type="Uniform Rectangular Grid",
                             user_name="DensOttawa1",
                             element=DensOttawaEle,
                             region=fm.region.get_region(0),
                             **{'X Min': Xmin, 'X Max': Xmax, 
                                'Y Min': Ymin, 'Y Max': Ymax, 
                                'Z Min': Zmin, 'Z Max': Zmin + thick1, 
                                'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': int(thick1/dz1)})
Zmin += thick1
fm.meshPart.create_mesh_part(category="Volume mesh",
                             mesh_part_type="Uniform Rectangular Grid",
                             user_name="DensOttawa2",
                            element=DensOttawaEle,
                            region=fm.region.get_region(0),
                            **{'X Min': Xmin, 'X Max': Xmax, 
                                'Y Min': Ymin, 'Y Max': Ymax, 
                                'Z Min': Zmin, 'Z Max': Zmin + thick2, 
                                'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': int(thick2/dz2)})

Zmin += thick2
fm.meshPart.create_mesh_part(category="Volume mesh",
                                mesh_part_type="Uniform Rectangular Grid",
                                user_name="DensOttawa3",
                                element=DensOttawaEle,
                                region=fm.region.get_region(0),
                                **{'X Min': Xmin, 'X Max': Xmax,
                                'Y Min': Ymin, 'Y Max': Ymax,
                                'Z Min': Zmin, 'Z Max': Zmin + thick3,
                                'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': int(thick3/dz3)})
Zmin += thick3
fm.meshPart.create_mesh_part(category="Volume mesh",
                                mesh_part_type="Uniform Rectangular Grid",
                                user_name="LooseOttawa",
                                element=LooseOttawaEle,
                                region=fm.region.get_region(0),
                                **{'X Min': Xmin, 'X Max': Xmax,
                                'Y Min': Ymin, 'Y Max': Ymax,
                                'Z Min': Zmin, 'Z Max': Zmin + thick4,
                                'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': int(thick4/dz4)})
Zmin += thick4
fm.meshPart.create_mesh_part(category="Volume mesh",
                                mesh_part_type="Uniform Rectangular Grid",
                                user_name="Montrey",
                                element=MontreyEle,
                                region=fm.region.get_region(0),
                                **{'X Min': Xmin, 'X Max': Xmax,
                                'Y Min': Ymin, 'Y Max': Ymax,
                                'Z Min': Zmin, 'Z Max': Zmin + thick5,  
                                'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': int(thick5/dz5)})



#  Create assembly Sections
fm.assembler.create_section(meshparts=["DensOttawa1", "DensOttawa2", "DensOttawa3"], num_partitions=2)
fm.assembler.create_section(["LooseOttawa"], num_partitions=2)
fm.assembler.create_section(["Montrey"], num_partitions=2)

# Assemble the mesh parts
fm.assembler.Assemble()


# Create a TimeSeries for the uniform excitation
timeseries = fm.timeSeries.create_time_series(series_type="path",filePath="kobe.acc",fileTime="kobe.time")

# Create a pattern for the uniform excitation
kobe = fm.pattern.create_pattern(pattern_type="uniformexcitation",dof=1, time_series=timeseries)


# boundary conditions
fm.constraint.mp.create_laminar_boundary(dofs=[1,2], direction=3)
fm.constraint.sp.fixMacroZmin(dofs=[1,2,3])


# Create a recorder for the whole model
recorder = fm.recorder.create_recorder("vtkhdf", file_base_name="result.vtkhdf",resp_types=["disp", "vel", "accel", "stress3D6", "strain3D6", "stress2D3", "strain2D3"], delta_t=0.02)

# Create a gravity analysis step
gravity = fm.analysis.create_default_transient_analysis(username="gravity", dt=0.01, num_steps=50)


# Add the recorder and gravity analysis step to the process
fm.process.add_step(kobe, description="Uniform Excitation (Kobe record)")
fm.process.add_step(recorder, description="Recorder of the whole model")
fm.process.add_step(gravity, description="Gravity Analysis Step")


fm.export_to_tcl("mesh.tcl")
fm.gui()

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

FEMORA provides a comprehensive implementation of the Domain Reduction Method for efficient seismic wave propagation analysis with absorbing boundary layers:

```python
# Define mesh parts and materials as in previous examples
# ...

# Assemble mesh parts
fm.assembler.create_section(mesh_parts, num_partitions=4)
fm.assembler.Assemble()

# Add absorbing boundary layer using PML (Perfectly Matched Layer)
fm.drm.addAbsorbingLayer(
    numLayers=4,             # Number of layers in absorbing boundary
    numPartitions=8,         # Number of partitions for parallel processing
    partitionAlgo="kd-tree", # Partitioning algorithm
    geometry="Rectangular",  # Geometry of the domain
    rayleighDamping=0.95,    # Rayleigh damping coefficient
    matchDamping=False,      # Whether to match damping with adjacent layers
    type="PML"               # Type of absorbing boundary (PML or Rayleigh)
)

# Create H5DRM pattern for seismic loading
h5pattern = fm.pattern.create_pattern(
    'h5drm',
    filepath='drmload.h5drm',
    factor=1.0,
    crd_scale=1.0,
    distance_tolerance=0.01,
    do_coordinate_transformation=1,
    transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
    origin=[0.0, 0.0, 0.0]
)

# Set up DRM-specific process with the pattern
fm.drm.set_pattern(h5pattern)
fm.drm.createDefaultProcess(finalTime=30, dT=0.01)

# Export to OpenSees TCL file and visualize
fm.export_to_tcl(filename="model.tcl")
fm.gui()
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