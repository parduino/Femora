"""
Section GUI Utilities
Common utilities for section GUI dialogs
"""

from qtpy.QtWidgets import QComboBox
from femora.components.Material.materialBase import Material


def setup_material_dropdown(combo_box: QComboBox, material_filter=None, placeholder_text="Select Material"):
    """
    Helper function to populate material dropdown with filtered materials
    
    Args:
        combo_box (QComboBox): ComboBox to populate
        material_filter (callable, optional): Filter function to select specific material types
                                            Example: lambda mat: mat.material_type == 'uniaxialMaterial'
        placeholder_text (str): Text for the placeholder option
    """
    combo_box.clear()
    combo_box.addItem(placeholder_text, None)
    
    all_materials = Material.get_all_materials()
    
    if not all_materials:
        combo_box.addItem("No materials available", None)
        combo_box.setEnabled(False)
        return
    
    combo_box.setEnabled(True)
    
    # Sort materials by name for better user experience
    sorted_materials = sorted(all_materials.items(), key=lambda x: x[1].user_name.lower())
    
    for tag, material in sorted_materials:
        # Apply filter if provided
        if material_filter and not material_filter(material):
            continue
            
        # Create descriptive display name
        display_name = f"{material.user_name} (Tag: {tag}, Type: {material.material_type} - {material.material_name})"
        combo_box.addItem(display_name, material)


def setup_concrete_material_dropdown(combo_box: QComboBox):
    """
    Set up dropdown for concrete materials (nDMaterial types)
    """
    def is_concrete_material(mat):
        return (mat.material_type == 'nDMaterial' and 
                ('concrete' in mat.user_name.lower() or 
                 'elastic' in mat.material_name.lower()))
    
    setup_material_dropdown(combo_box, is_concrete_material, "Select Concrete Material")


def setup_steel_material_dropdown(combo_box: QComboBox):
    """
    Set up dropdown for steel materials (typically uniaxialMaterial types)
    """
    def is_steel_material(mat):
        return (mat.material_type == 'uniaxialMaterial' and 
                ('steel' in mat.user_name.lower() or 
                 'rebar' in mat.user_name.lower() or
                 'elastic' in mat.material_name.lower()))
    
    setup_material_dropdown(combo_box, is_steel_material, "Select Steel Material")


def setup_any_material_dropdown(combo_box: QComboBox):
    """
    Set up dropdown for any available materials
    """
    setup_material_dropdown(combo_box, None, "Select Any Material")


def get_material_by_combo_selection(combo_box: QComboBox):
    """
    Get the selected material from a combo box
    
    Args:
        combo_box (QComboBox): ComboBox with material selection
        
    Returns:
        Material or None: Selected material object or None if no selection
    """
    return combo_box.currentData()


def set_combo_to_material(combo_box: QComboBox, material):
    """
    Set combo box selection to a specific material
    
    Args:
        combo_box (QComboBox): ComboBox to update
        material (Material): Material to select
    """
    if material is None:
        combo_box.setCurrentIndex(0)  # Select placeholder
        return
    
    for i in range(combo_box.count()):
        if combo_box.itemData(i) == material:
            combo_box.setCurrentIndex(i)
            return
    
    # If material not found, add it and select it
    display_name = f"{material.user_name} (Tag: {material.tag}, Type: {material.material_type} - {material.material_name})"
    combo_box.addItem(display_name, material)
    combo_box.setCurrentIndex(combo_box.count() - 1)


def validate_material_selection(combo_box: QComboBox, field_name="Material"):
    """
    Validate that a material is selected in the combo box
    
    Args:
        combo_box (QComboBox): ComboBox to validate
        field_name (str): Name of the field for error messages
        
    Returns:
        tuple: (is_valid: bool, material: Material or None, error_message: str)
    """
    material = get_material_by_combo_selection(combo_box)
    
    if material is None:
        return False, None, f"Please select a {field_name.lower()}."
    
    return True, material, ""


def refresh_all_material_dropdowns(*combo_boxes):
    """
    Refresh multiple material dropdowns
    
    Args:
        *combo_boxes: Variable number of QComboBox objects to refresh
    """
    for combo_box in combo_boxes:
        current_selection = get_material_by_combo_selection(combo_box)
        # Assume the combo box has a setup function attribute or use generic setup
        setup_any_material_dropdown(combo_box)
        if current_selection:
            set_combo_to_material(combo_box, current_selection)


# Material type filters for common use cases
MATERIAL_FILTERS = {
    'any': None,
    'concrete': lambda mat: (mat.material_type == 'nDMaterial' and 
                            ('concrete' in mat.user_name.lower() or 
                             'elastic' in mat.material_name.lower())),
    'steel': lambda mat: (mat.material_type == 'uniaxialMaterial' and 
                         ('steel' in mat.user_name.lower() or 
                          'rebar' in mat.user_name.lower() or
                          'elastic' in mat.material_name.lower())),
    'uniaxial': lambda mat: mat.material_type == 'uniaxialMaterial',
    'nDMaterial': lambda mat: mat.material_type == 'nDMaterial',
}


def setup_filtered_material_dropdown(combo_box: QComboBox, filter_type: str):
    """
    Set up material dropdown with predefined filter
    
    Args:
        combo_box (QComboBox): ComboBox to populate
        filter_type (str): Type of filter ('any', 'concrete', 'steel', 'uniaxial', 'nDMaterial')
    """
    if filter_type not in MATERIAL_FILTERS:
        raise ValueError(f"Unknown filter type: {filter_type}. Available: {list(MATERIAL_FILTERS.keys())}")
    
    filter_func = MATERIAL_FILTERS[filter_type]
    placeholder = f"Select {filter_type.title()} Material" if filter_type != 'any' else "Select Material"
    
    setup_material_dropdown(combo_box, filter_func, placeholder)


def setup_uniaxial_material_dropdown(combo_box: QComboBox, placeholder_text="Select Uniaxial Material"):
    """
    Set up dropdown for uniaxial materials only (for RCSection materials)
    """
    def is_uniaxial(mat):
        return mat.material_type == 'uniaxialMaterial'
    setup_material_dropdown(combo_box, is_uniaxial, placeholder_text)


if __name__ == "__main__":
    print("Section GUI Utilities - for use in section dialog files")
    print("Available functions:")
    print("- setup_material_dropdown()")
    print("- setup_concrete_material_dropdown()")
    print("- setup_steel_material_dropdown()")
    print("- setup_any_material_dropdown()")
    print("- validate_material_selection()")
    print("- refresh_all_material_dropdowns()")