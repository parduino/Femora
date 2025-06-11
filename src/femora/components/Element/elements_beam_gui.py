"""
Beam Element GUI Components for FEMORA
Handles creation and editing of beam-column elements with sections and transformations
"""

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QCheckBox,
    QMessageBox, QGroupBox
)
from qtpy.QtCore import Qt

from femora.components.Element.elementBase import ElementRegistry
from femora.components.section.section_base import Section, SectionManager
from femora.components.transformation.transformation import GeometricTransformation, GeometricTransformationManager
from femora.components.transformation.transformation_gui import TransformationWidget3D


def setup_section_dropdown(combo_box, placeholder_text="Select Section"):
    """Setup dropdown with available sections"""
    combo_box.clear()
    combo_box.addItem(placeholder_text)
    
    sections = Section.get_all_sections()
    for section in sections.values():
        display_text = f"{section.user_name} ({section.section_name})"
        combo_box.addItem(display_text, section)


def validate_section_selection(combo_box, field_name="Section"):
    """Validate section selection from combo box"""
    if combo_box.currentIndex() == 0:
        return False, None, f"Please select a {field_name.lower()}."
    
    section = combo_box.currentData()
    if section is None:
        return False, None, f"Invalid {field_name.lower()} selection."
    
    return True, section, ""


class BeamElementCreationDialog(QDialog):
    """Dialog for creating beam-column elements"""
    
    def __init__(self, element_type, parent=None):
        super().__init__(parent)
        self.element_type = element_type
        self.setWindowTitle(f"Create {element_type} Element")
        self.created_element = None
        
        # Get element class
        self.element_class = ElementRegistry._element_types[element_type]
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout for main inputs
        form_layout = QFormLayout()
        
        # DOF selection
        self.dof_combo = QComboBox()
        if hasattr(self.element_class, 'get_possible_dofs'):
            dofs = self.element_class.get_possible_dofs()
            if not dofs:
                dofs = ["3", "6"]
        else:
            dofs = ["3", "6"]  # Default for beam elements
        self.dof_combo.addItems(dofs)
        form_layout.addRow("Degrees of Freedom:", self.dof_combo)
        
        # Section selection
        self.section_combo = QComboBox()
        setup_section_dropdown(self.section_combo)
        form_layout.addRow("Section:", self.section_combo)
        
        layout.addLayout(form_layout)
        
        # Transformation widget (3D)
        self.transformation_widget = TransformationWidget3D()
        layout.addWidget(QLabel("Geometric Transformation:"))
        layout.addWidget(self.transformation_widget)
        
        # Parameters group
        self.setup_parameters_group(layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create Element")
        create_btn.clicked.connect(self.create_element)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def setup_parameters_group(self, main_layout):
        """Setup element-specific parameters"""
        params_group = QGroupBox("Element Parameters")
        params_layout = QGridLayout(params_group)
        
        self.param_inputs = {}
        parameters = self.element_class.get_parameters()
        descriptions = self.element_class.get_description()
        
        for row, (param, desc) in enumerate(zip(parameters, descriptions)):
            param_label = QLabel(param + ":")
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            desc_label.setWordWrap(True)
            
            if param == "cMass":
                # Special handling for boolean cMass parameter
                param_input = QCheckBox("Use consistent mass matrix")
            else:
                param_input = QLineEdit()
                param_input.setPlaceholderText(f"Enter {param}")
            
            params_layout.addWidget(param_label, row, 0)
            params_layout.addWidget(param_input, row, 1)
            params_layout.addWidget(desc_label, row, 2)
            
            self.param_inputs[param] = param_input
        
        main_layout.addWidget(params_group)
    
    def create_element(self):
        """Create the beam element"""
        try:
            # Validate DOF
            dof = int(self.dof_combo.currentText())
            
            # Validate section
            is_valid, section, error_msg = validate_section_selection(self.section_combo)
            if not is_valid:
                QMessageBox.warning(self, "Input Error", error_msg)
                return
            
            # Get transformation from widget
            transformation = self.transformation_widget.get_transformation()
            if transformation is None:
                QMessageBox.warning(self, "Input Error", "Please provide a valid geometric transformation.")
                return
            
            # Collect parameters
            params = {}
            for param, input_field in self.param_inputs.items():
                if param == "cMass":
                    params[param] = input_field.isChecked()
                else:
                    value = input_field.text().strip()
                    if value:
                        params[param] = value
            
            # Validate parameters
            if params:
                params = self.element_class.validate_element_parameters(**params)
            
            # Create element
            self.created_element = ElementRegistry.create_element(
                element_type=self.element_type,
                ndof=dof,
                section=section,
                transformation=transformation,
                **params
            )
            
            QMessageBox.information(self, "Success", 
                                  f"{self.element_type} element created successfully!")
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create element: {str(e)}")


class BeamElementEditDialog(QDialog):
    """Dialog for editing beam-column elements"""
    
    def __init__(self, element, parent=None):
        super().__init__(parent)
        self.element = element
        self.setWindowTitle(f"Edit {element.element_type} Element (Tag: {element.tag})")
        
        self.setup_ui()
        self.load_current_values()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout for main inputs
        form_layout = QFormLayout()
        
        # DOF selection
        self.dof_combo = QComboBox()
        if hasattr(self.element.__class__, 'get_possible_dofs'):
            dofs = self.element.__class__.get_possible_dofs()
            if not dofs:
                dofs = ["3", "6"]
        else:
            dofs = ["3", "6"]
        self.dof_combo.addItems(dofs)
        form_layout.addRow("Degrees of Freedom:", self.dof_combo)
        
        # Section selection
        self.section_combo = QComboBox()
        setup_section_dropdown(self.section_combo)
        form_layout.addRow("Section:", self.section_combo)
        
        layout.addLayout(form_layout)
        
        # Transformation widget
        self.transformation_widget = TransformationWidget3D()
        layout.addWidget(QLabel("Geometric Transformation:"))
        layout.addWidget(self.transformation_widget)
        
        # Parameters group
        self.setup_parameters_group(layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def setup_parameters_group(self, main_layout):
        """Setup element-specific parameters"""
        params_group = QGroupBox("Element Parameters")
        params_layout = QGridLayout(params_group)
        
        self.param_inputs = {}
        parameters = self.element.__class__.get_parameters()
        descriptions = self.element.__class__.get_description()
        
        for row, (param, desc) in enumerate(zip(parameters, descriptions)):
            param_label = QLabel(param + ":")
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            desc_label.setWordWrap(True)
            
            if param == "cMass":
                param_input = QCheckBox("Use consistent mass matrix")
            else:
                param_input = QLineEdit()
                param_input.setPlaceholderText(f"Enter {param}")
            
            params_layout.addWidget(param_label, row, 0)
            params_layout.addWidget(param_input, row, 1)
            params_layout.addWidget(desc_label, row, 2)
            
            self.param_inputs[param] = param_input
        
        main_layout.addWidget(params_group)
    
    def load_current_values(self):
        """Load current element values into the form"""
        # Set DOF
        self.dof_combo.setCurrentText(str(self.element._ndof))
        
        # Set section
        current_section = self.element._section
        for i in range(self.section_combo.count()):
            section = self.section_combo.itemData(i)
            if section and section.tag == current_section.tag:
                self.section_combo.setCurrentIndex(i)
                break
        
        # Set transformation in widget
        current_transformation = self.element._transformation
        self.transformation_widget.load_transformation(current_transformation)
        
        # Set parameters
        current_values = self.element.get_values(self.element.__class__.get_parameters())
        for param, input_field in self.param_inputs.items():
            if param in current_values:
                value = current_values[param]
                if param == "cMass":
                    input_field.setChecked(bool(value))
                else:
                    input_field.setText(str(value))
    
    def save_changes(self):
        """Save changes to the element"""
        try:
            # Validate section
            is_valid, section, error_msg = validate_section_selection(self.section_combo)
            if not is_valid:
                QMessageBox.warning(self, "Input Error", error_msg)
                return
            
            # Get transformation from widget
            transformation = self.transformation_widget.get_transformation()
            if transformation is None:
                QMessageBox.warning(self, "Input Error", "Please provide a valid geometric transformation.")
                return
            
            # Collect parameters
            params = {}
            for param, input_field in self.param_inputs.items():
                if param == "cMass":
                    params[param] = input_field.isChecked()
                else:
                    value = input_field.text().strip()
                    if value:
                        params[param] = value
            
            # Add section and transformation to update values
            params["section"] = section
            params["transformation"] = transformation
            
            # Update element
            self.element.update_values(params)
            
            # Update DOF if changed
            new_dof = int(self.dof_combo.currentText())
            if new_dof != self.element._ndof:
                self.element._ndof = new_dof
            
            QMessageBox.information(self, "Success", 
                                  f"Element '{self.element.tag}' updated successfully!")
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update element: {str(e)}")


# Helper function to determine if element is a beam element
def is_beam_element(element_type):
    """Check if element type is a beam element"""
    beam_types = [
        'elasticbeamcolumn',
        'dispbeamcolumn',
        'nonlinearbeamcolumn',
        'forcebasedbeamcolumn'
    ]
    return element_type.lower() in beam_types


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    import sys
    from femora.components.section.section_opensees import ElasticSection
    from femora.components.transformation.transformation import GeometricTransformation3D

    app = QApplication(sys.argv)

    # Create test data
    section = ElasticSection(user_name="Test Section", E=200000, A=0.01, Iz=1e-6)
    transformation = GeometricTransformation3D(
        transf_type="Linear",
        vecxz_x=1, vecxz_y=0, vecxz_z=-1,
        d_xi=0, d_yi=0, d_zi=0,
        d_xj=1, d_yj=0, d_zj=0
    )

    # Test creation dialog
    creation_dialog = BeamElementCreationDialog("ElasticBeamColumn")
    creation_dialog.show()

    # If you want to test the edit dialog, you need a dummy element instance.
    # Here is an example assuming your element class is ElasticBeamColumn and takes these arguments:
    from femora.components.Element.elements_opensees_beam import ElasticBeamColumnElement

    # Create a dummy element for editing
    dummy_element = ElasticBeamColumnElement(ndof=6, section=section, transformation=transformation)
    # Test edit dialog
    edit_dialog = BeamElementEditDialog(dummy_element)
    edit_dialog.show()

    sys.exit(app.exec())
