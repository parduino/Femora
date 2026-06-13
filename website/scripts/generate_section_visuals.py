import os
import sys
from pathlib import Path

# Add src directory to path so we can import femora
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from femora.core.model import Model

def main():
    assets_dir = Path(__file__).parents[1] / "docs" / "assets" / "sections"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize femora model
    model = Model()
    
    # Materials for sections
    concr_core = model.material.uniaxial.elastic(user_name="CoreConcrete", E=3600.0)
    steel = model.material.uniaxial.steel01(
        user_name="RebarSteel",
        Fy=60.0,
        E0=29000.0,
        b=0.01,
    )
    
    # 1. Custom Rectangular Fiber Section (Concrete core + corner rebars)
    rect_sec = model.section.fiber.section(user_name="Manual_RectSection")
    if rect_sec.tag is None:
        rect_sec.tag = 1
        
    rect_sec.add_rectangular_patch(
        material=concr_core,
        num_subdiv_y=10,
        num_subdiv_z=10,
        y1=-8.0,
        z1=-8.0,
        y2=8.0,
        z2=8.0,
    )
    # Add 4 corner rebars
    rect_sec.add_fiber(y_loc=-7.0, z_loc=-7.0, area=0.79, material=steel)
    rect_sec.add_fiber(y_loc=-7.0, z_loc=7.0, area=0.79, material=steel)
    rect_sec.add_fiber(y_loc=7.0, z_loc=-7.0, area=0.79, material=steel)
    rect_sec.add_fiber(y_loc=7.0, z_loc=7.0, area=0.79, material=steel)
    
    rect_sec.plot(
        save_path=str(assets_dir / "section_rect.png"),
        title="Custom Rectangular Fiber Section",
        material_colors={"CoreConcrete": "#7f7f7f", "RebarSteel": "#d62728"}
    )
    print("Generated section_rect.png")
    
    # 2. Circular Fiber Section (Concrete circle + circle of rebars)
    circ_sec = model.section.fiber.section(user_name="Circular_ColumnSection")
    if circ_sec.tag is None:
        circ_sec.tag = 2
        
    circ_sec.add_circular_patch(
        material=concr_core,
        num_subdiv_circ=16,
        num_subdiv_rad=8,
        y_center=0.0,
        z_center=0.0,
        int_rad=0.0,
        ext_rad=10.0,
    )
    circ_sec.add_circular_layer(
        material=steel,
        num_fibers=12,
        area_per_fiber=0.79,
        y_center=0.0,
        z_center=0.0,
        radius=8.5,
    )
    
    circ_sec.plot(
        save_path=str(assets_dir / "section_circ.png"),
        title="Circular Column Fiber Section",
        material_colors={"CoreConcrete": "#7f7f7f", "RebarSteel": "#d62728"}
    )
    print("Generated section_circ.png")

if __name__ == "__main__":
    main()
