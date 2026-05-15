import pytest
import femora as fm
import pyvista as pv
import numpy as np


# material 
mat = fm.material.nd.elastic_isotropic(name="mat1", E=20000, nu=0.3, rho=1.9)


# element
ele = fm.element.brick.std(ndof=3, 
                           material=mat, 
                           b1= 0.0, b2= 0.0, b3= 0.0,
                           lumped=True)



# meshPart:
dx = 1.0
dy = 1.0
dz = 1.0
xmin = -5.0
xmax = 5.0
ymin = -5.0
ymax = 5.0
zmin = -5.0
zmax = 0.0
embedded_depth = 2.0
embedded_xmin = -2.0
embedded_xmax = 2.0
embedded_ymin = -2.0
embedded_ymax = 2.0

scale = 2.0
# scale the dimensions of the embedded region
xmin *= scale
xmax *= scale
ymin *= scale
ymax *= scale
zmin *= scale
zmax *= scale
embedded_xmin *= scale
embedded_xmax *= scale
embedded_ymin *= scale
embedded_ymax *= scale
embedded_depth *= scale



# checking the validity of embeedded region
assert embedded_xmin > xmin and embedded_xmax < xmax, "Embedded region in x-direction is invalid"
assert embedded_ymin > ymin and embedded_ymax < ymax, "Embedded region in y-direction is invalid"
assert embedded_depth < (zmax - zmin), "Embedded region in z-direction is invalid"



fm.meshPart.volume.uniform_rectangular_grid(user_name="part1", 
                                            element=ele,
                                            region=None,
                                            x_min=xmin, x_max=xmax,
                                            y_min=ymin, y_max=embedded_ymin,
                                            z_min=zmin, z_max=zmax,
                                            nx = int((xmax - xmin)/dx),
                                            ny = int((embedded_ymin - ymin)/dy),
                                            nz = int((zmax - zmin)/dz)
                                            )

fm.meshPart.volume.uniform_rectangular_grid(user_name="part2", 
                                                element=ele,
                                                region=None,
                                                x_min=xmin, x_max=xmax, 
                                                y_min=embedded_ymax, y_max=ymax,
                                                z_min=zmin, z_max=zmax,
                                                nx = int((xmax - xmin)/dx),
                                                ny = int((ymax - embedded_ymax)/dy),
                                                nz = int((zmax - zmin)/dz)
                                                )

fm.meshPart.volume.uniform_rectangular_grid(user_name="part3",
                                            element=ele,
                                            region=None,
                                            x_min=xmin, x_max=embedded_xmin,
                                            y_min=embedded_ymin, y_max=embedded_ymax,
                                            z_min=zmin, z_max=zmax,
                                            nx = int((embedded_xmin - xmin)/dx),
                                            ny = int((embedded_ymax - embedded_ymin)/dy),
                                            nz = int((zmax - zmin)/dz)
                                            )

fm.meshPart.volume.uniform_rectangular_grid(user_name="part4",
                                            element=ele,
                                            region=None,
                                            x_min=embedded_xmax, x_max=xmax,
                                            y_min=embedded_ymin, y_max=embedded_ymax,
                                            z_min=zmin, z_max=zmax,
                                            nx = int((xmax - embedded_xmax)/dx),
                                            ny = int((embedded_ymax - embedded_ymin)/dy),
                                            nz = int((zmax - zmin)/dz)
                                            )

fm.meshPart.volume.uniform_rectangular_grid(user_name="part5",
                                            element=ele,
                                            region=None,
                                            x_min=embedded_xmin, x_max=embedded_xmax,   
                                            y_min=embedded_ymin, y_max=embedded_ymax,
                                            z_min=zmin, z_max=zmax - embedded_depth,
                                            nx = int((embedded_xmax - embedded_xmin)/dx),
                                            ny = int((embedded_ymax - embedded_ymin)/dy),   
                                            nz = int((zmax - zmin - embedded_depth)/dz)
                                            )

fm.meshPart.volume.uniform_rectangular_grid(user_name="foundation",
                                            element=ele,
                                            region=None,
                                            x_min=embedded_xmin, x_max=embedded_xmax,
                                            y_min=embedded_ymin, y_max=embedded_ymax,
                                            z_min=(zmax - embedded_depth),
                                            z_max=zmax,
                                            nx = 2*int((embedded_xmax - embedded_xmin)/dx),
                                            ny = 2*int((embedded_ymax - embedded_ymin)/dy),
                                            nz = 2*int((embedded_depth)/dz) 
                                            )                                            

# fm.meshPart.volume.uniform_rectangular_grid(user_name="foundation1",
#                                             element=ele,
#                                             region=None,
#                                             x_min=embedded_xmin, x_max=0,
#                                             y_min=embedded_ymin, y_max=0,
#                                             z_min=(zmax - embedded_depth),
#                                             z_max=zmax,
#                                             nx = 2*int((embedded_xmax - embedded_xmin)/dx),
#                                             ny = 2*int((embedded_ymax - embedded_ymin)/dy),
#                                             nz = 2*int((embedded_depth)/dz) 
#                                             )
# fm.meshPart.volume.uniform_rectangular_grid(user_name="foundation2",
#                                             element=ele,
#                                             region=None,
#                                             x_min=0, x_max=embedded_xmax,
#                                             y_min=0, y_max=embedded_ymax,
#                                             z_min=(zmax - embedded_depth),
#                                             z_max=zmax,
#                                             nx = 3*int((embedded_xmax - embedded_xmin)/dx),
#                                             ny = 3*int((embedded_ymax - embedded_ymin)/dy),
#                                             nz = 3*int((embedded_depth)/dz) 
#                                             )


# fm.mesh_part.volume.uniform_rectangular_grid(user_name="foundation3",
#                                             element=ele,
#                                             region=None,
#                                             x_min=0, x_max=embedded_xmax,
#                                             y_min=embedded_ymin, y_max=0,
#                                             z_min=(zmax - embedded_depth),
#                                             z_max=zmax,
#                                             nx = 4*int((embedded_xmax - embedded_xmin)/dx),
#                                             ny = 4*int((embedded_ymax - embedded_ymin)/dy),
#                                             nz = 4*int((embedded_depth)/dz) 
#                                             )

# fm.mesh_part.volume.uniform_rectangular_grid(user_name="foundation4",
#                                             element=ele,
#                                             region=None,
#                                             x_min=embedded_xmin, x_max=0,
#                                             y_min=0, y_max=embedded_ymax,
#                                             z_min=(zmax - embedded_depth),
#                                             z_max=zmax,
#                                             nx = 5*int((embedded_xmax - embedded_xmin)/dx),
#                                             ny = 5*int((embedded_ymax - embedded_ymin)/dy),
#                                             nz = 5*int((embedded_depth)/dz) 
#                                             )


                                


# part4 = fm.meshPart.volume.uniform_rectangular_grid(user_name="foundation4",
#                                             element=ele,
#                                             region=None,
#                                             x_min=embedded_xmin, x_max=embedded_xmax,
#                                             y_min=embedded_ymin, y_max=embedded_ymax,
#                                             z_min=(zmax - embedded_depth),
#                                             z_max=zmax,
#                                             nx = 4*int((embedded_xmax - embedded_xmin)/dx),
#                                             ny = 4*int((embedded_ymax - embedded_ymin)/dy),
#                                             nz = 4*int((embedded_depth)/dz) 
#                                             )

# part2.transform.rotate_z(angle=45, point=(embedded_xmax/2., embedded_ymax/2., zmax))


fm.assembler.create_section(["part1", 
                            "part2",
                            "part3", 
                            "part4", 
                            "part5",
                            ], 
                            num_partitions=8)
fm.assembler.create_section(["foundation"], num_partitions=2)
# fm.assembler.create_section(["foundation1","foundation2"], num_partitions=2)
# fm.assembler.create_section(["foundation3","foundation4"], num_partitions=2)
fm.interface.node_interface(
    name="interface1",
    constrained_node="foundation", 
    # retained_nodes=["part5"],
    offset=0.1,
    normal_filter=[1,0,0],
    filter_tolerance=0.98,)
fm.assembler.Assemble(merge_points=False)
# fm.assembler.plot(show_edges=True, scalars="MeshPartTag_celldata")
fm.export_to_tcl("test_embededd_node.tcl")







