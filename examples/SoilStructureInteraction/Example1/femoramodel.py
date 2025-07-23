import femora as fm

# ==========================================================
# Soil 
# ==========================================================
soil_mat = fm.material.nd.elastic_isotropic(
    user_name="soil_mat",
    E=2e8, # Young's modulus in Pa
    nu=0.4, # Poisson's ratio
    rho = 2100.0 # Density in kg/m^3
)
dx = 0.5
dy = dx ; dz = dx
Xmin = -8.0; Xmax = 8.0; 
Ymin = -3.0; Ymax = 3.0;
Zmin = -8.0; Zmax = 0.0;
Nx = int((Xmax - Xmin) / dx)
Ny = int((Ymax - Ymin) / dy)
Nz = int((Zmax - Zmin) / dz)
soilele = fm.element.brick.std(
    name="soil_brick",
    material=soil_mat,
    ndof=3)

fm.mesh_part.volume.uniform_rectangular_grid(
    user_name="soil_grid",
    element=soilele,
    region=None,
    **{
    "X Min": Xmin, "X Max": Xmax,
    "Y Min": Ymin, "Y Max": Ymax,
    "Z Min": Zmin, "Z Max": Zmax,
    "Nx Cells": Nx, "Ny Cells": Ny, "Nz Cells": Nz,
    })


# ==========================================================
# Beam 
# ==========================================================
# transformation
transf = fm.transformation.transformation3d(
    transf_type="PDelta",
    vecxz_x=-1,
    vecxz_y=0,
    vecxz_z=0,
)

# Pile section definition
diameter = 1.5  # pile diameter in meters
radius  = diameter / 2.0
pi      = 3.141593
Epile   = 1e10  # Young's modulus for the pile material in Pa
nu      = 0.3  # Poisson's ratio for the pile material
Gpile   = Epile / (2 * (1 + nu))  # Shear modulus
Area    = (diameter ** 2) * pi / 2.0  # Cross-sectional area
Iy      = (diameter ** 4) * pi / 64.0  # Moment of inertia about y-axis
Iz      = (diameter ** 4) * pi / 64.0  # Moment of inertia about z-axis
Jpile   = (diameter ** 4) * pi / 32.0  # Polar moment of inertia
pile_sec = fm.section.elastic(
    user_name="pile_section",
    E=Epile,
    nu=nu,
    G=Gpile,
    A=Area,
    Iy=Iy,
    Iz=Iz,
    J=Jpile,
)
pile_ele = fm.element.beam.disp(
    ndof=6,
    section=pile_sec,
    transformation=transf,
    numIntgrPts=5,
)

fm.mesh_part.line.single_line(
    user_name="pile",
    element=pile_ele,
    region=None,
    x0 = 0.0,
    y0 = 0.0,
    z0 = -5.0,
    x1 = 0.0,
    y1 = 0.0,
    z1 = 2.0,
    number_of_lines = 16,
    merge_points = True,
)
# ==========================================================
# interface 
# ==========================================================
fm.interface.beam_solid_interface(
    name = "pile_soil_interface",
    beam_part = "pile",
    solid_parts = None,  # No solid part specified
    radius = radius,  # Interface radius
    n_peri = 8,
    n_long = 5,
    penalty_param = 1.0e12,  # Penalty parameter
    g_penalty = True,  # Use geometric penalty
)


# ==========================================================
# Assembly
# ==========================================================
fm.assembler.create_section(
    meshparts=["soil_grid", "pile"],
    num_partitions=2,
    partition_algorithm="kd-tree",
    merging_points=False,
)
fm.assembler.Assemble()

# ==========================================================
# PML Layer
# ==========================================================
fm.drm.addAbsorbingLayer(numLayers=4,
                        numPartitions=8,
                        partitionAlgo="kd-tree",
                        geometry="Rectangular",
                        rayleighDamping=0.95,
                        matchDamping=False,
                        type="PML",
                        )

h5pattern = fm.pattern.create_pattern( 'h5drm',
                                        filepath='drmload.h5drm',
                                        factor=1.0,
                                        crd_scale=1.0,
                                        distance_tolerance=0.01,
                                        do_coordinate_transformation=1,
                                        transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
                                        origin=[0.0, 0.0, 0.0])
fm.drm.set_pattern(h5pattern)
fm.drm.createDefaultProcess(finalTime=30, dT=0.01)
fm.export_to_tcl(filename="model.tcl")
fm.gui()


