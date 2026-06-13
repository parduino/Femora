import os
import sys
from pathlib import Path

# Add src directory to path so we can import femora
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

import pyvista as pv
from femora.core.model import Model

def setup_plotter(title):
    pl = pv.Plotter(off_screen=True, window_size=[800, 600])
    
    # Premium background color matching light theme
    pl.background_color = "#fbf8f6"
    
    # Coordinate grid and axes for spatial context
    pl.show_grid(
        color="#c4b1a8",
        grid="back",
        xtitle="X",
        ytitle="Y",
        ztitle="Z"
    )
    pl.show_axes()
    
    pl.add_text(title, position="upper_left", font_size=10, color="#342b27")
    return pl

def export_plotter(pl, output_path):
    pl.view_isometric()
    pl.reset_camera()
    pl.camera.zoom(1.1)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pl.export_html(str(output_path))
    pl.close()

def main():
    assets_dir = Path(__file__).parents[1] / "docs" / "assets" / "meshparts"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize femora model
    model = Model()
    
    # --- Generate STEP 3: Family examples ---
    
    # 1. Volume family (matching doc: nx=10, ny=10, nz=10)
    soil_nd = model.material.nd.elastic_isotropic(
        user_name="soft_soil",
        E=5.0e4,
        nu=0.30,
        rho=1.8,
    )
    brick_el = model.element.brick.std(
        ndof=3,
        material=soil_nd,
    )
    volume_part = model.meshpart.volume.uniform_rectangular_grid(
        user_name="soil_box",
        element=brick_el,
        x_min=-5.0,
        x_max=5.0,
        y_min=-5.0,
        y_max=5.0,
        z_min=-10.0,
        z_max=0.0,
        nx=10,
        ny=10,
        nz=10,
    )
    volume_part.generate_mesh()
    
    pl = setup_plotter("Volume Mesh Part (soil_box)")
    pl.add_mesh(
        volume_part.mesh,
        color="#a97461",
        show_edges=True,
        edge_color="#ffffff",
        line_width=1.0,
    )
    export_plotter(pl, assets_dir / "family_volume.html")
    print("Generated family_volume.html")
    
    # 2. Line family
    section = model.section.beam.elastic(
        user_name="column_section",
        E=2.0e8,
        A=0.25,
        Iz=0.01,
        Iy=0.01,
        G=8.0e7,
        J=0.02,
    )
    transf = model.transformation.transformation3d(
        transf_type="Linear",
        vecxz_x=1.0,
        vecxz_y=0.0,
        vecxz_z=0.0,
    )
    beam_el = model.element.beam.disp(
        ndof=6,
        section=section,
        transformation=transf,
    )
    line_part = model.meshpart.line.single_line(
        user_name="column_1",
        element=beam_el,
        x0=0.0,
        y0=0.0,
        z0=0.0,
        x1=0.0,
        y1=0.0,
        z1=5.0,
        number_of_lines=5,
    )
    line_part.generate_mesh()
    
    pl = setup_plotter("Line Mesh Part (column)")
    pl.add_mesh(
        line_part.mesh,
        color="#a97461",
        line_width=6.0,
        render_lines_as_tubes=True,
    )
    pl.add_mesh(
        line_part.mesh,
        color="#342b27",
        style="points",
        point_size=12.0,
        render_points_as_spheres=True,
    )
    export_plotter(pl, assets_dir / "family_line.html")
    print("Generated family_line.html")
    
    # 3. Surface family
    quad_el = model.element.quad.ssp(
        ndof=2,
        material=soil_nd,
        Type="PlaneStrain",
        Thickness=1.0,
    )
    # Workaround for case-sensitive CircularOGrid2D element check
    quad_el.element_type = "sspquad"
    
    surface_part = model.meshpart.surface.circular_o_grid(
        user_name="foundation_surface",
        element=quad_el,
        R=5.0,
        r0_ratio=0.35,
        nt=16,
        nr=4,
    )
    surface_part.generate_mesh()
    
    pl = setup_plotter("Surface Mesh Part (foundation_surface)")
    pl.add_mesh(
        surface_part.mesh,
        color="#a97461",
        show_edges=True,
        edge_color="#ffffff",
        line_width=2.0,
    )
    export_plotter(pl, assets_dir / "family_surface.html")
    print("Generated family_surface.html")
    
    # 4. External family
    cylinder_mesh = pv.Cylinder(radius=2.0, height=5.0, direction=(0.0, 0.0, 1.0)).triangulate()
    external_part = model.meshpart.general.external_mesh(
        user_name="imported_domain",
        element=brick_el,
        mesh=cylinder_mesh,
    )
    external_part.generate_mesh()
    
    pl = setup_plotter("External Mesh Part (imported_domain)")
    pl.add_mesh(
        external_part.mesh,
        color="#a97461",
        show_edges=True,
        edge_color="#ffffff",
        line_width=2.0,
    )
    export_plotter(pl, assets_dir / "family_external.html")
    print("Generated family_external.html")
    
    # --- Generate STEP 4: Transformations (using nx=10, ny=10, nz=10) ---
    
    # Original mesh for comparison wireframe
    original_mesh = volume_part.mesh.copy()
    
    # 5. Original state (solid block, no wireframe comparison needed)
    pl = setup_plotter("Original soil box")
    pl.add_mesh(
        original_mesh,
        color="#a97461",
        show_edges=True,
        edge_color="#ffffff",
        line_width=1.0,
    )
    export_plotter(pl, assets_dir / "soil_box_original.html")
    print("Generated soil_box_original.html")
    
    # 6. Translated state
    pl = setup_plotter("Translated soil box ([12, 0, 0])")
    # Original as blue wireframe
    pl.add_mesh(
        original_mesh,
        color="#2680eb",
        style="wireframe",
        line_width=1.5,
        opacity=0.6,
    )
    # Translated
    translated_part = model.meshpart.volume.uniform_rectangular_grid(
        user_name="soil_box_t", element=brick_el,
        x_min=-5.0, x_max=5.0, y_min=-5.0, y_max=5.0, z_min=-10.0, z_max=0.0,
        nx=10, ny=10, nz=10
    )
    translated_part.generate_mesh()
    translated_part.transform.translate([12.0, 0.0, 0.0])
    
    pl.add_mesh(
        translated_part.mesh,
        color="#a97461",
        show_edges=True,
        edge_color="#ffffff",
        line_width=1.0,
    )
    export_plotter(pl, assets_dir / "soil_box_translated.html")
    print("Generated soil_box_translated.html")
    
    # 7. Rotated state
    pl = setup_plotter("Rotated soil box (15 degrees about Z)")
    # Original as blue wireframe
    pl.add_mesh(
        original_mesh,
        color="#2680eb",
        style="wireframe",
        line_width=1.5,
        opacity=0.6,
    )
    # Rotated
    rotated_part = model.meshpart.volume.uniform_rectangular_grid(
        user_name="soil_box_r", element=brick_el,
        x_min=-5.0, x_max=5.0, y_min=-5.0, y_max=5.0, z_min=-10.0, z_max=0.0,
        nx=10, ny=10, nz=10
    )
    rotated_part.generate_mesh()
    rotated_part.transform.rotate_z(15.0)
    
    pl.add_mesh(
        rotated_part.mesh,
        color="#a97461",
        show_edges=True,
        edge_color="#ffffff",
        line_width=1.0,
    )
    export_plotter(pl, assets_dir / "soil_box_rotated.html")
    print("Generated soil_box_rotated.html")
    
    # 8. Translated + Rotated state
    pl = setup_plotter("Translated + Rotated soil box")
    # Original as blue wireframe
    pl.add_mesh(
        original_mesh,
        color="#2680eb",
        style="wireframe",
        line_width=1.5,
        opacity=0.6,
    )
    # Translated + Rotated
    tr_part = model.meshpart.volume.uniform_rectangular_grid(
        user_name="soil_box_tr", element=brick_el,
        x_min=-5.0, x_max=5.0, y_min=-5.0, y_max=5.0, z_min=-10.0, z_max=0.0,
        nx=10, ny=10, nz=10
    )
    tr_part.generate_mesh()
    tr_part.transform.translate([12.0, 0.0, 0.0])
    tr_part.transform.rotate_z(15.0)
    
    pl.add_mesh(
        tr_part.mesh,
        color="#a97461",
        show_edges=True,
        edge_color="#ffffff",
        line_width=1.0,
    )
    export_plotter(pl, assets_dir / "soil_box_translated_rotated.html")
    print("Generated soil_box_translated_rotated.html")

if __name__ == "__main__":
    main()
