"""
Elastic Section GUI Dialogs
Uses ElasticSection class methods instead of hardcoding
"""

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QFormLayout, QMessageBox, 
    QGridLayout, QFrame, QTextBrowser, QGroupBox, QWidget
)
from qtpy.QtCore import Qt

from femora.components.section.section_opensees import ElasticSection
from femora.components.Material.materialBase import Material

# Import utilities if available
try:
    from .section_gui_utils import (
        setup_material_dropdown, validate_material_selection, 
        get_material_by_combo_selection, set_combo_to_material
    )
except ImportError:
    # Fallback implementations if utilities not available
    def setup_material_dropdown(combo_box, material_filter=None, placeholder_text="Select Material"):
        combo_box.clear()
        combo_box.addItem(placeholder_text, None)
        for tag, material in Material.get_all_materials().items():
            if material_filter and not material_filter(material):
                continue
            display_name = f"{material.user_name} (Tag: {tag})"
            combo_box.addItem(display_name, material)
    
    def validate_material_selection(combo_box, field_name="Material"):
        material = combo_box.currentData()
        if material is None:
            return False, None, f"Please select a {field_name.lower()}."
        return True, material, ""
    
    def get_material_by_combo_selection(combo_box):
        return combo_box.currentData()
    
    def set_combo_to_material(combo_box, material):
        for i in range(combo_box.count()):
            if combo_box.itemData(i) == material:
                combo_box.setCurrentIndex(i)
                return


class ElasticSectionCreationDialog(QDialog):
    """
    Dialog for creating new Elastic sections using ElasticSection class methods
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Elastic Section")
        self.setMinimumSize(800, 600)
        
        # Get parameters and descriptions from the ElasticSection class
        self.parameters = ElasticSection.get_parameters()
        self.descriptions = ElasticSection.get_description()
        
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
            
            # Parameter input
            param_input = QLineEdit()
            param_input.setPlaceholderText(f"Enter {param}")
            
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
        help_display.setHtml(ElasticSection.get_help_text())
        right_layout.addWidget(help_display)
        
        main_layout.addWidget(right_widget)
        
        # Set layout proportions (left side wider than right)
        main_layout.setStretch(0, 3)
        main_layout.setStretch(2, 2)

    def create_section(self):
        """Create the elastic section using class validation methods"""
        try:
            # Validate section name
            user_name = self.user_name_input.text().strip()
            if not user_name:
                QMessageBox.warning(self, "Input Error", "Please enter a section name.")
                return
            
            # Check if name already exists
            try:
                existing_section = ElasticSection.get_section_by_name(user_name)
                QMessageBox.warning(self, "Input Error", f"Section with name '{user_name}' already exists.")
                return
            except KeyError:
                pass  # Name is available
            
            # Collect parameters from input fields
            params = {}
            for param, input_field in self.param_inputs.items():
                value = input_field.text().strip()
                if value:  # Only include non-empty values
                    params[param] = value
            
            # Use the class validation method
            try:
                validated_params = ElasticSection.validate_section_parameters(**params)
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
                return
            
            # Create the section using validated parameters
            self.created_section = ElasticSection(user_name=user_name, **validated_params)
            
            QMessageBox.information(self, "Success", f"Elastic section '{user_name}' created successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create section: {str(e)}")


class ElasticSectionEditDialog(QDialog):
    """
    Dialog for editing existing Elastic sections using class methods
    """
    def __init__(self, section, parent=None):
        super().__init__(parent)
        self.section = section
        self.setWindowTitle(f"Edit Elastic Section: {section.user_name}")
        self.setMinimumSize(800, 600)
        
        # Get parameters and descriptions from the section class
        self.parameters = section.get_parameters()
        self.descriptions = section.get_description()
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        
        # Left side - Parameters
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Section info group (read-only)
        info_group = QGroupBox("Section Information")
        info_layout = QFormLayout(info_group)
        
        self.tag_label = QLabel(str(section.tag))
        self.user_name_label = QLabel(section.user_name)
        self.type_label = QLabel(section.section_name)
        
        info_layout.addRow("Tag:", self.tag_label)
        info_layout.addRow("Name:", self.user_name_label)
        info_layout.addRow("Type:", self.type_label)
        
        left_layout.addWidget(info_group)
        
        # Get current parameter values using class method
        current_values = section.get_values(self.parameters)
        
        # Parameters group - dynamically created from class methods
        parameters_group = QGroupBox("Section Parameters")
        parameters_layout = QGridLayout(parameters_group)
        
        # Store input widgets for later access
        self.param_inputs = {}
        
        # Create inputs dynamically based on class parameters
        for row, (param, description) in enumerate(zip(self.parameters, self.descriptions)):
            # Parameter label
            param_label = QLabel(f"{param}:")
            
            # Parameter input with current value
            param_input = QLineEdit()
            current_value = current_values.get(param)
            if current_value is not None:
                param_input.setText(str(current_value))
            param_input.setPlaceholderText(f"Enter {param}")
            
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
        help_display.setHtml(section.__class__.get_help_text())
        right_layout.addWidget(help_display)
        
        main_layout.addWidget(right_widget)
        
        # Set layout proportions
        main_layout.setStretch(0, 3)
        main_layout.setStretch(2, 2)

    def save_changes(self):
        """Save changes using class validation and update methods"""
        try:
            # Collect parameters from input fields
            params = {}
            for param, input_field in self.param_inputs.items():
                value = input_field.text().strip()
                if value:  # Only include non-empty values
                    params[param] = value
            
            # Use the class validation method
            try:
                validated_params = self.section.__class__.validate_section_parameters(**params)
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
                return
            
            # Update the section using class method
            self.section.update_values(validated_params)
            
            QMessageBox.information(self, "Success", f"Section '{self.section.user_name}' updated successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update section: {str(e)}")


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Test creation dialog
    dialog = ElasticSectionCreationDialog()
    if dialog.exec() == QDialog.Accepted:
        print("Section created successfully!")
        
        # Test edit dialog with the created section
        if hasattr(dialog, 'created_section'):
            edit_dialog = ElasticSectionEditDialog(dialog.created_section)
            edit_dialog.exec()
    
    sys.exit(app.exec())