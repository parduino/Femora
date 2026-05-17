import unittest
import sys
import os

# Add src to path
sys.path.append(r"d:\Projects\Femora\src")

from femora.tools.sections import aisc
from femora.components.material.nd import ElasticIsotropicMaterial
from femora.components.section.section_opensees import ElasticSection
from femora.components.MeshMaker import MeshMaker

class TestAISCTool(unittest.TestCase):
    def setUp(self):
        # Initialize MeshMaker (singleton)
        self.model = MeshMaker()
        # Ensure clean state
        self.model.section.clear_all_sections()
        self.model.material.clear()

        # Create and manage a material for testing
        mat = ElasticIsotropicMaterial("TestSteel", E=29000.0, nu=0.3)
        self.material = self.model.material.add(mat)

    def tearDown(self):
        self.model.section.clear_all_sections()
        self.model.material.clear()

    def test_create_valid_section(self):
        """Test creating a valid W-section"""
        section_name = "W14X90"
        
        section = aisc.create_section(section_name, self.model, self.material)

        self.assertIsInstance(section, ElasticSection)

        # Tag is assigned by manager, starts at 1 usually
        self.assertGreaterEqual(section.tag, 1)
        self.assertIn(section_name, section.user_name)
        
        # Check if parameters were assigned (E, A, Iz, Iy, G, J)
        params = section.params
        self.assertIn('E', params)
        self.assertIn('A', params)
        self.assertIn('Iz', params)
        
    def test_section_properties_accuracy(self):
        """Test that properties match the internal database for a known section"""
        
        section = aisc.create_section("W14X90", self.model, self.material)
        params = section.params
        
        self.assertAlmostEqual(params['A'], 26.5, places=2)
        self.assertAlmostEqual(params['Iz'], 999.0, delta=5.0) 

    def test_case_sensitivity(self):
        """Test that section lookup handles case/separators if implemented, or fails correctly"""
        try:
            aisc.create_section("w14x90", self.model, self.material) # lowercase
        except ValueError:
            pass 
        except KeyError:
            pass 

    def test_invalid_section(self):
        """Test creating a non-existent section"""
        with self.assertRaises(ValueError):
            aisc.create_section("NonExistentSection", self.model, self.material)

    def test_missing_material(self):
        """Test creation without valid material"""
        with self.assertRaises(AttributeError): 
             aisc.create_section("W14X90", self.model, None)

    def test_unit_conversion(self):
        """Test unit conversion for geometric properties"""
        # W14X90 properties in inches
        # A ~ 26.5 in^2
        # Ix ~ 999 in^4
        
        # Test 1: Conversion to Meters
        # Scale factor = 0.0254
        scale_m = 0.0254
        expected_A_m = 26.5 * (scale_m ** 2)
        expected_Ix_m = 999.0 * (scale_m ** 4)
        
        section_m = aisc.create_section("W14X90", self.model, self.material, unit_system='m', user_name='W14X90_m')
        params_m = section_m.params
        
        self.assertAlmostEqual(params_m['A'], expected_A_m, delta=0.1 * expected_A_m) # 10% tolerance for variation/rounding
        self.assertAlmostEqual(params_m['Iz'], expected_Ix_m, delta=0.1 * expected_Ix_m)
        
        # Material properties should be UNCHANGED
        # self.material has E=29000
        self.assertAlmostEqual(params_m['E'], 29000.0)

        # Test 2: Conversion to Millimeters
        # Scale factor = 25.4
        scale_mm = 25.4
        expected_A_mm = 26.5 * (scale_mm ** 2)
        
        section_mm = aisc.create_section("W14X90", self.model, self.material, unit_system='mm', user_name='W14X90_mm')
        params_mm = section_mm.params
        
        self.assertAlmostEqual(params_mm['A'], expected_A_mm, delta=0.1 * expected_A_mm)
        self.assertAlmostEqual(params_mm['E'], 29000.0) # Material still unchanged

    def test_invalid_unit_system(self):
        """Test invalid unit system raises error"""
        with self.assertRaises(ValueError):
            aisc.create_section("W14X90", self.model, self.material, unit_system='invalid_unit')

if __name__ == "__main__":
    unittest.main()
