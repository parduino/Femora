import sys
import os
import traceback

sys.path.append(r"d:\Projects\Femora\src")

try:
    print("Importing aisc...")
    from femora.tools.sections import aisc
    print("Importing ElasticIsotropicMaterial...")
    from femora.components.material.nd import ElasticIsotropicMaterial
    print("Importing ElasticSection...")
    from femora.components.section.section_opensees import ElasticSection
    
    print("Creating material...")
    mat = ElasticIsotropicMaterial("TestSteel", E=29000.0, nu=0.3)
    
    print("Creating section...")
    sec = aisc.create_section("W14X90", mat, section_tag=1)
    print(f"Section created: {sec.user_name}")
    
except Exception:
    with open("debug_error.log", "w") as f:
        traceback.print_exc(file=f)
    traceback.print_exc()
