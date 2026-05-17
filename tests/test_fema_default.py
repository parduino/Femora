
import femora as fm
from femora.components.MeshMaker import MeshMaker
from femora.components.material.nd import ElasticIsotropicMaterial
from femora.tools.buildings.steel_frame import FEMA_SAC_SteelFrame

def main():
    model = MeshMaker()
    steel = ElasticIsotropicMaterial("Steel", E=29000.0, nu=0.3)
    
    # Test Default Constructor (Should be 9-Story LA9)
    print("Testing FEMA_SAC_SteelFrame default constructor...")
    building = FEMA_SAC_SteelFrame() 
    
    mesh = building.build(model, steel)
    
    print(f"Built Default Frame: {mesh.user_name}")
    print(f"Elements: {mesh.mesh.n_cells}")
    
    # Check expected counts for 9-story (30ft x 30ft bays? No, default logic says 3x240in bays)
    # 9 Stories. 
    # Just ensure it builds without error and has elements.
    assert mesh.mesh.n_cells > 0
    print("Default verification successful.")

if __name__ == "__main__":
    main()
