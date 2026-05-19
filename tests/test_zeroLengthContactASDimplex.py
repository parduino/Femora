
import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..', 'src'))
sys.path.append(src_dir)

from femora.components.element.zero_length_contact import ZeroLengthContactASDimplex
from femora.core.element_base import Element

def test_zeroLengthContactASDimplex():
    print("Testing ZeroLengthContactASDimplex Element...")

    # 1. Create element with minimal params
    # ndof can be 2, 3, 4, 6. Using 3 for test.
    Kn = 1.0e10
    Kt = 1.0e8
    mu = 0.5
    from femora.components.MeshMaker import MeshMaker
    mm = MeshMaker()
    mm.clear_model()
    ele1 = mm.element.special.zero_length_contact(ndof=3, Kn=Kn, Kt=Kt, mu=mu)
    tcl1 = ele1.to_tcl(tag=100, nodes=[10, 20])
    print(f"Minimal TCL: {tcl1}")

    expected1 = f"element zeroLengthContactASDimplex 100 10 20 {Kn} {Kt} {mu}"
    if tcl1 != expected1:
        print(f"Error: expected '{expected1}', got '{tcl1}'")
        sys.exit(1)
    # 2. Create element with all params
    intType = 1
    orient = [0.0, 1.0, 0.0]
    ele2 = mm.element.special.zero_length_contact(ndof=3, Kn=Kn, Kt=Kt, mu=mu, intType=intType, orient=orient)
    tcl2 = ele2.to_tcl(tag=200, nodes=[30, 40])
    print(f"Full TCL: {tcl2}")
    
    # Check parts
    if f"{Kn} {Kt} {mu}" not in tcl2:
        print("Error: Material properties missing or incorrect")
        sys.exit(1)
    if "-intType 1" not in tcl2:
        print("Error: -intType flag missing or incorrect")
        sys.exit(1)
    if "-orient 0.0 1.0 0.0" not in tcl2:
        print("Error: -orient flag missing or incorrect")
        sys.exit(1)

    print("All tests passed!")

if __name__ == "__main__":
    test_zeroLengthContactASDimplex()
