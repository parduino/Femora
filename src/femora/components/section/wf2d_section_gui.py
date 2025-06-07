"""
WFSection2d GUI Dialogs
Uses WFSection2d class methods instead of hardcoding
"""

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QFormLayout, QMessageBox, 
    QGridLayout, QFrame, QTextBrowser, QGroupBox, QWidget
)
from qtpy.QtCore import Qt

from femora.components.section.section_opensees import WFSection2d
from femora.components.Material.materialBase import Material

# Import utilities if available
from femora.components.section.section_gui_utils import (
    setup_material_dropdown, validate_material_selection,
    get_material_by_combo_selection, set_combo_to_material,
    setup_filtered_material_dropdown
)


class WFSection2dCreationDialog(QDialog):
    """
    Dialog for creating new WFSection2d sections using WFSection2d class methods
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create WF Section 2D")
        self.setMinimumSize(800, 600)
        
        # Get parameters and descriptions from the WFSection2d class
        self.parameters = WFSection2d.get_parameters()
        self.descriptions = WFSection2d.get_description()
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        
        # Left side - Parameters
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Section name group
        name_group = QGroupBox("Section Identification")
        name_layout = QFormLayout(name_group)
        
        self.user_name_input = QLineEdit()
        self.user_name_input.setPlaceholderText("Enter unique section name")
        name_layout.addRow("Section Name:", self.user_name_input)
        
        left_layout.addWidget(name_group)
        
        # Parameters group - dynamically created from class methods
        parameters_group = QGroupBox("Section Parameters")
        parameters_layout = QGridLayout(parameters_group)
        
        # Store input widgets for later access
        self.param_inputs = {}
        
        # Create inputs dynamically based on class parameters
        for row, (param, description) in enumerate(zip(self.parameters, self.descriptions)):
            # Parameter label
            param_label = QLabel(f"{param}:")
            
            # Special handling for material parameter
            if param == "material":
                # Material selection dropdown
                param_input = QComboBox()
                setup_filtered_material_dropdown(param_input, 'uniaxial')
                param_input.setToolTip("Select a uniaxial material for the WF section")
            else:
                # Regular text input for other parameters
                param_input = QLineEdit()
                param_input.setPlaceholderText(f"Enter {param}")
                
                # Add specific tooltips for numeric parameters
                if param in ['Nflweb', 'Nflflange']:
                    param_input.setToolTip("Enter a positive integer")
                else:
                    param_input.setToolTip("Enter a positive number")
            
            # Description label
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            
            # Add to layout
            parameters_layout.addWidget(param_label, row, 0)
            parameters_layout.addWidget(param_input, row, 1)
            parameters_layout.addWidget(desc_label, row, 2)
            
            # Store for later access
            self.param_inputs[param] = param_input
        
        left_layout.addWidget(parameters_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create Section")
        create_btn.clicked.connect(self.create_section)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        left_layout.addLayout(btn_layout)
        
        # Add stretch to push buttons to bottom
        left_layout.addStretch()
        
        main_layout.addWidget(left_widget)
        
        # Vertical line separator
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Right side - Help text from class
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        help_display = QTextBrowser()
        help_display.setHtml(WFSection2d.get_help_text())
        right_layout.addWidget(help_display)
        
        main_layout.addWidget(right_widget)
        
        # Set layout proportions (left side wider than right)
        main_layout.setStretch(0, 3)
        main_layout.setStretch(2, 2)

    def create_section(self):
        """Create the WFSection2d section using class validation methods"""
        try:
            # Validate section name
            user_name = self.user_name_input.text().strip()
            if not user_name:
                QMessageBox.warning(self, "Input Error", "Please enter a section name.")
                return
            
            # Check if name already exists
            try:
                existing_section = WFSection2d.get_section_by_name(user_name)
                QMessageBox.warning(self, "Input Error", f"Section with name '{user_name}' already exists.")
                return
            except KeyError:
                pass  # Name is available
            
            # Collect parameters from input fields
            params = {}
            material = None
            
            for param, input_field in self.param_inputs.items():
                if param == "material":
                    # Validate material selection
                    is_valid, material, error_msg = validate_material_selection(input_field, "Material")
                    if not is_valid:
                        QMessageBox.warning(self, "Input Error", error_msg)
                        return
                    # Don't add material to params dict, handle separately
                else:
                    # Handle other parameters
                    value = input_field.text().strip()
                    if value:  # Only include non-empty values
                        params[param] = value
            
            # Validate that material was selected
            if material is None:
                QMessageBox.warning(self, "Input Error", "Please select a material.")
                return
            
            # Use the class validation method for numeric parameters
            try:
                validated_params = WFSection2d.validate_section_parameters(**params)
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
                return
            
            # Create the section using validated parameters and material
            self.created_section = WFSection2d(user_name=user_name, material=material, **validated_params)
            
            QMessageBox.information(self, "Success", f"WF Section 2D '{user_name}' created successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create section: {str(e)}")


class WFSection2dEditDialog(QDialog):
    """
    Dialog for editing existing WFSection2d sections using class methods
    """
    def __init__(self, section, parent=None):
        super().__init__(parent)
        self.section = section
        self.setWindowTitle(f"Edit WF Section 2D: {section.user_name}")
        self.setMinimumSize(800, 600)
        
        # Get parameters and descriptions from the section class
        self.parameters = section.get_parameters()
        self.descriptions = section.get_description()
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        
        # Left side - Parameters
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Section name group (read-only for editing)
        name_group = QGroupBox("Section Identification")
        name_layout = QFormLayout(name_group)
        
        self.user_name_label = QLabel(section.user_name)
        self.user_name_label.setStyleSheet("font-weight: bold;")
        name_layout.addRow("Section Name:", self.user_name_label)
        
        left_layout.addWidget(name_group)
        
        # Parameters group - dynamically created from class methods
        parameters_group = QGroupBox("Section Parameters")
        parameters_layout = QGridLayout(parameters_group)
        
        # Store input widgets for later access
        self.param_inputs = {}
        
        # Get current values from the section
        current_values = section.get_values(self.parameters)
        
        # Create inputs dynamically based on class parameters
        for row, (param, description) in enumerate(zip(self.parameters, self.descriptions)):
            # Parameter label
            param_label = QLabel(f"{param}:")
            
            # Special handling for material parameter
            if param == "material":
                # Material selection dropdown
                param_input = QComboBox()
                setup_filtered_material_dropdown(param_input, 'uniaxial')
                param_input.setToolTip("Select a uniaxial material for the WF section")
                
                # Set current material
                if section.material:
                    set_combo_to_material(param_input, section.material)
            else:
                # Regular text input for other parameters
                param_input = QLineEdit()
                param_input.setPlaceholderText(f"Enter {param}")
                
                # Set current value
                current_value = current_values.get(param)
                if current_value is not None:
                    param_input.setText(str(current_value))
                
                # Add specific tooltips for numeric parameters
                if param in ['Nflweb', 'Nflflange']:
                    param_input.setToolTip("Enter a positive integer")
                else:
                    param_input.setToolTip("Enter a positive number")
            
            # Description label
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            
            # Add to layout
            parameters_layout.addWidget(param_label, row, 0)
            parameters_layout.addWidget(param_input, row, 1)
            parameters_layout.addWidget(desc_label, row, 2)
            
            # Store for later access
            self.param_inputs[param] = param_input
        
        left_layout.addWidget(parameters_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        left_layout.addLayout(btn_layout)
        
        # Add stretch to push buttons to bottom
        left_layout.addStretch()
        
        main_layout.addWidget(left_widget)
        
        # Vertical line separator
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Right side - Help text from class
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        help_display = QTextBrowser()
        help_display.setHtml(WFSection2d.get_help_text())
        right_layout.addWidget(help_display)
        
        main_layout.addWidget(right_widget)
        
        # Set layout proportions (left side wider than right)
        main_layout.setStretch(0, 3)
        main_layout.setStretch(2, 2)

    def save_changes(self):
        """Save changes to the WFSection2d section"""
        try:
            # Collect parameters from input fields
            params = {}
            material = None
            
            for param, input_field in self.param_inputs.items():
                if param == "material":
                    # Validate material selection
                    is_valid, material, error_msg = validate_material_selection(input_field, "Material")
                    if not is_valid:
                        QMessageBox.warning(self, "Input Error", error_msg)
                        return
                    # Don't add material to params dict, handle separately
                else:
                    # Handle other parameters
                    value = input_field.text().strip()
                    if value:  # Only include non-empty values
                        params[param] = value
            
            # Validate that material was selected
            if material is None:
                QMessageBox.warning(self, "Input Error", "Please select a material.")
                return
            
            # Prepare update values including material
            update_values = dict(params)
            update_values['material'] = material
            
            # Update the section using its update_values method
            self.section.update_values(update_values)
            
            QMessageBox.information(self, "Success", "Section updated successfully!")
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update section: {str(e)}")


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial
    
    app = QApplication(sys.argv)
    
    # Create a test material
    steel = ElasticUniaxialMaterial(user_name="Steel", E=200000, eta=0.0)
    
    # Test creation dialog
    dialog = WFSection2dCreationDialog()
    if dialog.exec() == QDialog.Accepted:
        print("Section created successfully!")
    
    sys.exit(app.exec())
