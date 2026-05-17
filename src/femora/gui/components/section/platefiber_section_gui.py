"""
Plate Fiber Section GUI Dialogs
Uses PlateFiberSection class methods instead of hardcoding
"""

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QFormLayout, QMessageBox, QGridLayout, QFrame, QTextBrowser, QGroupBox, QWidget
)
from qtpy.QtCore import Qt

from femora.components.section.section_opensees import PlateFiberSection
from femora.components.section.section_gui_utils import setup_material_dropdown, get_material_by_combo_selection, set_combo_to_material, validate_material_selection

class PlateFiberSectionCreationDialog(QDialog):
    """
    Dialog for creating new PlateFiberSection sections using class methods
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Plate Fiber Section")
        self.setMinimumSize(800, 600)
        
        self.parameters = PlateFiberSection.get_parameters()
        self.descriptions = PlateFiberSection.get_description()
        
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
        
        # Parameters group
        parameters_group = QGroupBox("Section Parameters")
        parameters_layout = QGridLayout(parameters_group)
        self.param_inputs = {}
        
        for row, (param, description) in enumerate(zip(self.parameters, self.descriptions)):
            param_label = QLabel(f"{param}:")
            if param == "material":
                param_input = QComboBox()
                # Only nDMaterial (plane stress) materials are valid
                def is_nd_material(mat):
                    return mat.material_type == 'nDMaterial'
                setup_material_dropdown(param_input, is_nd_material, "Select NDMaterial (plane stress)")
                param_input.setToolTip("Select NDMaterial for plate fiber section")
            else:
                param_input = QLineEdit()
                param_input.setPlaceholderText(f"Enter {param}")
                param_input.setToolTip("Enter a value")
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            parameters_layout.addWidget(param_label, row, 0)
            parameters_layout.addWidget(param_input, row, 1)
            parameters_layout.addWidget(desc_label, row, 2)
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
        help_display.setHtml(PlateFiberSection.get_help_text())
        right_layout.addWidget(help_display)
        main_layout.addWidget(right_widget)
        main_layout.setStretch(0, 3)
        main_layout.setStretch(2, 2)

    def create_section(self):
        try:
            user_name = self.user_name_input.text().strip()
            if not user_name:
                QMessageBox.warning(self, "Input Error", "Please enter a section name.")
                return
            try:
                existing_section = PlateFiberSection.get_section_by_name(user_name)
                QMessageBox.warning(self, "Input Error", f"Section with name '{user_name}' already exists.")
                return
            except KeyError:
                pass
            # Material
            material = get_material_by_combo_selection(self.param_inputs["material"])
            if not material:
                QMessageBox.warning(self, "Input Error", "Please select a NDMaterial for the section.")
                return
            params = {"material": material}
            try:
                validated_params = PlateFiberSection.validate_section_parameters(**params)
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
                return
            self.created_section = PlateFiberSection(user_name=user_name, **params)
            QMessageBox.information(self, "Success", f"Plate Fiber Section '{user_name}' created successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create section: {str(e)}")

class PlateFiberSectionEditDialog(QDialog):
    """
    Dialog for editing existing PlateFiberSection sections using class methods
    """
    def __init__(self, section, parent=None):
        super().__init__(parent)
        self.section = section
        self.setWindowTitle(f"Edit Plate Fiber Section: {section.user_name}")
        self.setMinimumSize(800, 600)
        self.parameters = section.get_parameters()
        self.descriptions = section.get_description()
        main_layout = QHBoxLayout(self)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        info_group = QGroupBox("Section Information")
        info_layout = QFormLayout(info_group)
        self.tag_label = QLabel(str(section.tag))
        self.user_name_label = QLabel(section.user_name)
        self.type_label = QLabel(section.section_name)
        info_layout.addRow("Tag:", self.tag_label)
        info_layout.addRow("Name:", self.user_name_label)
        info_layout.addRow("Type:", self.type_label)
        left_layout.addWidget(info_group)
        current_values = section.get_values(self.parameters)
        parameters_group = QGroupBox("Section Parameters")
        parameters_layout = QGridLayout(parameters_group)
        self.param_inputs = {}
        for row, (param, description) in enumerate(zip(self.parameters, self.descriptions)):
            param_label = QLabel(f"{param}:")
            if param == "material":
                param_input = QComboBox()
                def is_nd_material(mat):
                    return mat.material_type == 'nDMaterial'
                setup_material_dropdown(param_input, is_nd_material, "Select NDMaterial (plane stress)")
                set_combo_to_material(param_input, section.material)
                param_input.setToolTip("Select NDMaterial for plate fiber section")
            else:
                param_input = QLineEdit()
                current_value = current_values.get(param)
                if current_value is not None:
                    param_input.setText(str(current_value))
                param_input.setPlaceholderText(f"Enter {param}")
                param_input.setToolTip("Enter a value")
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            parameters_layout.addWidget(param_label, row, 0)
            parameters_layout.addWidget(param_input, row, 1)
            parameters_layout.addWidget(desc_label, row, 2)
            self.param_inputs[param] = param_input
        left_layout.addWidget(parameters_group)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        left_layout.addLayout(btn_layout)
        left_layout.addStretch()
        main_layout.addWidget(left_widget)
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        help_display = QTextBrowser()
        help_display.setHtml(section.__class__.get_help_text())
        right_layout.addWidget(help_display)
        main_layout.addWidget(right_widget)
        main_layout.setStretch(0, 3)
        main_layout.setStretch(2, 2)
    def save_changes(self):
        try:
            material = get_material_by_combo_selection(self.param_inputs["material"])
            if not material:
                QMessageBox.warning(self, "Input Error", "Please select a NDMaterial for the section.")
                return
            update_values = {"material": material}
            self.section.update_values(update_values)
            QMessageBox.information(self, "Success", f"Section '{self.section.user_name}' updated successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update section: {str(e)}")
