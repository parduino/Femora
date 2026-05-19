import sys
import os
import pytest
from typing import Optional

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'src'))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from femora.components.element import ZeroLengthContactASDimplex
from femora.core.element_base import Element

@pytest.fixture(autouse=True)
def setup_teardown():
    Element.clear_all_elements()
    yield
    Element.clear_all_elements()

def test_zl_contact_initialization():
    """Test valid initialization."""
    ele = ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=2e8, mu=0.5)

    assert ele.tag is None
    assert ele.Kn == 1e8
    assert ele.Kt == 2e8
    assert ele.mu == 0.5
    assert ele.intType == 0
    assert ele.orient is None

def test_zl_contact_options():
    """Test optional parameters."""
    # With orient and intType
    ele = ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=1e8, mu=0.5, 
                                     orient=[1, 0, 0], intType=1)
    
    assert ele.orient == [1.0, 0.0, 0.0]
    assert ele.intType == 1

def test_zl_contact_invalid_inputs():
    """Test invalid inputs."""
    # Invalid orient
    with pytest.raises(ValueError, match="orient must be a list"):
        ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=1e8, mu=0.5, orient="invalid")

    with pytest.raises(ValueError, match="orient must be a list"):
        ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=1e8, mu=0.5, orient=[1, 2])
    with pytest.raises(ValueError, match="requires 2, 3, 4, or 6 DOFs"):
        ZeroLengthContactASDimplex(ndof=5, Kn=1e8, Kt=1e8, mu=0.5)
    with pytest.raises(ValueError, match="Kn must be positive"):
        ZeroLengthContactASDimplex(ndof=3, Kn=0.0, Kt=1e8, mu=0.5)
    with pytest.raises(ValueError, match="Kt must be positive"):
        ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=0.0, mu=0.5)
    with pytest.raises(ValueError, match="mu must be non-negative"):
        ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=1e8, mu=-0.1)
    with pytest.raises(ValueError, match="intType must be 0 or 1"):
        ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=1e8, mu=0.5, intType=2)

def test_zl_contact_to_tcl():
    """Test TCL generation."""
    nodes = [10, 20]
    
    # Basic
    ele = ZeroLengthContactASDimplex(ndof=3, Kn=100.0, Kt=200.0, mu=0.3)
    tcl = ele.to_tcl(tag=1, nodes=nodes)
    expected = "element zeroLengthContactASDimplex 1 10 20 100.0 200.0 0.3"
    assert tcl == expected

    # With options
    ele_opt = ZeroLengthContactASDimplex(ndof=3, Kn=100.0, Kt=200.0, mu=0.3,
                                         orient=[0, 1, 0], intType=1)
    tcl_opt = ele_opt.to_tcl(tag=2, nodes=nodes)
    # Order: basic ... -orient ... -intType ...
    expected_opt = "element zeroLengthContactASDimplex 2 10 20 100.0 200.0 0.3 -orient 0.0 1.0 0.0 -intType 1"
    assert tcl_opt == expected_opt

    # Incorrect nodes
    with pytest.raises(ValueError):
        ele.to_tcl(tag=1, nodes=[10, 20, 30])
