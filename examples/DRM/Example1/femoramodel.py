import os
import femora as fm
os.chdir(os.path.dirname(__file__))



# create one damping for all the meshParts
uniformDamp = fm.damping.frequencyRayleigh(f1 = 2.76, f2 = 13.84, dampingFactor=0.03)
region = fm.region.elementRegion(damping=uniformDamp)

# defining the mesh parts
Xmin = -5.0 ;Xmax = 5.0
Ymin = -5.0 ;Ymax = 5.0
Zmin = -18.;Zmax = 0.0
dx   = 1.0; dy   = 1.0
Nx = int((Xmax - Xmin)/dx)
Ny = int((Ymax - Ymin)/dy)


layers_properties = [
    {"user_name": "Dense Ottawa1",  "G": 145.0e6, "gamma": 19.9,  "nu": 0.3, "thickness": 2.6, "dz": 1.3}, 
    {"user_name": "Dense Ottawa2",  "G": 145.0e6, "gamma": 19.9,  "nu": 0.3, "thickness": 2.4, "dz": 1.2},
    {"user_name": "Dense Ottawa3",  "G": 145.0e6, "gamma": 19.9,  "nu": 0.3, "thickness": 5.0, "dz": 1.0},
    {"user_name": "Loose Ottawa",   "G": 75.0e6,  "gamma": 19.1,  "nu": 0.3, "thickness": 6.0, "dz": 0.5}, 
    {"user_name": "Dense Montrey",  "G": 42.0e6,  "gamma": 19.8,  "nu": 0.3, "thickness": 2.0, "dz": 0.5} 
]


for layer in layers_properties:
    name = layer["user_name"]
    nu   = layer["nu"]
    rho  = layer["gamma"] * 1000 / 9.81        # Density in kg/m^3
    Vs   = (layer["G"] / rho) ** 0.5           # Shear wave velocity in m/s
    E    = 2 * layer["G"] * (1 + layer["nu"])  # Young's modulus in Pa
    E    = E / 1000.                           # Convert to kPa
    rho  = rho / 1000.                         # Convert to kg/m^3

    print(f"Layer: {name}, Vs: {Vs}")


    # Define the material
    fm.material.create_material(material_category="nDMaterial", material_type="ElasticIsotropic", user_name=name, E=E, nu=nu, rho=rho)

    # Define the element
    ele = fm.element.create_element(element_type="stdBrick", ndof=3, material=name, b1=0.0, b2=0.0, b3=-9.81 * rho)

    fm.meshPart.create_mesh_part(category="Volume mesh", mesh_part_type="Uniform Rectangular Grid", 
                                 user_name=name, element=ele, region=region,
                                **{
                                    'X Min': Xmin, 'X Max': Xmax,
                                    'Y Min': Ymin, 'Y Max': Ymax,
                                    'Z Min': Zmin, 'Z Max': Zmin + layer["thickness"],
                                    'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': int(layer["thickness"] / layer["dz"])
                                })
    Zmin += layer["thickness"]


# #  Create assembly Sections
fm.assembler.create_section(meshparts=[layer["user_name"] for layer in layers_properties], num_partitions=0)


# Assemble the mesh parts
fm.assembler.Assemble()

fm.assembler.Assemble()
fm.drm.addAbsorbingLayer(numLayers=1,
                        numPartitions=0,
                        partitionAlgo="kd-tree",
                        geometry="Rectangular",
                        rayleighDamping=0.95,
                        matchDamping=False,
                        type="Rayleigh",
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

