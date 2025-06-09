"""
Aggregator Section GUI Dialogs
Uses AggregatorSection class methods instead of hardcoding
"""

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QFormLayout, QMessageBox, QGridLayout, QFrame, QTextBrowser, QGroupBox, QWidget
)

from femora.components.section.section_opensees import AggregatorSection
from femora.components.section.section_base import Section
from femora.components.section.section_gui_utils import setup_material_dropdown, get_material_by_combo_selection, set_combo_to_material, setup_uniaxial_material_dropdown


class AggregatorSectionCreationDialog(QDialog):
    """
    Dialog for creating new AggregatorSection sections using class methods
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Aggregator Section")
        self.setMinimumSize(500, 400)
        self.response_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
        
        self.parameters = AggregatorSection.get_parameters()
        self.descriptions = AggregatorSection.get_description()
        
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
        
        # Materials group
        materials_group = QGroupBox("Materials by Response Code")
        materials_layout = QGridLayout(materials_group)
        self.material_combos = {}
        for row, code in enumerate(self.response_codes):
            code_label = QLabel(f"{code}:")
            combo = QComboBox()
            setup_uniaxial_material_dropdown(combo, "Select Uniaxial Material")
            materials_layout.addWidget(code_label, row, 0)
            materials_layout.addWidget(combo, row, 1)
            self.material_combos[code] = combo
        left_layout.addWidget(materials_group)
        
        # Base section group (optional)
        base_section_group = QGroupBox("Base Section (Optional)")
        base_section_layout = QFormLayout(base_section_group)
        self.base_section_combo = QComboBox()
        self.base_section_combo.addItem("None", None)
        for tag, section in Section.get_all_sections().items():
            self.base_section_combo.addItem(f"{section.user_name} (Tag: {tag})", section)
        base_section_layout.addRow("Base Section:", self.base_section_combo)
        left_layout.addWidget(base_section_group)
        
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
        help_display.setHtml(AggregatorSection.get_help_text())
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
                existing_section = AggregatorSection.get_section_by_name(user_name)
                QMessageBox.warning(self, "Input Error", f"Section with name '{user_name}' already exists.")
                return
            except KeyError:
                pass
            # Collect materials
            materials = {}
            for code, combo in self.material_combos.items():
                material = get_material_by_combo_selection(combo)
                if material:
                    materials[code] = material
            if not materials:
                QMessageBox.warning(self, "Input Error", "Please select at least one material for a response code.")
                return
            # Base section
            base_section = self.base_section_combo.currentData()
            params = {"materials": materials}
            if base_section:
                params["base_section"] = base_section
            try:
                validated_params = AggregatorSection.validate_section_parameters(**params)
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
                return
            self.created_section = AggregatorSection(user_name=user_name, **params)
            QMessageBox.information(self, "Success", f"Aggregator Section '{user_name}' created successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create section: {str(e)}")

class AggregatorSectionEditDialog(QDialog):
    """
    Dialog for editing existing AggregatorSection sections using class methods
    """
    def __init__(self, section, parent=None):
        super().__init__(parent)
        self.response_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
        self.section = section
        self.setWindowTitle(f"Edit Aggregator Section: {section.user_name}")
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
        # Materials group
        materials_group = QGroupBox("Materials by Response Code")
        materials_layout = QGridLayout(materials_group)
        self.material_combos = {}
        current_materials = section.materials if hasattr(section, 'materials') else {}
        for row, code in enumerate(self.response_codes):
            code_label = QLabel(f"{code}:")
            combo = QComboBox()
            setup_material_dropdown(combo, lambda m: m.material_type == 'uniaxialMaterial', "Select Material")
            if code in current_materials:
                set_combo_to_material(combo, current_materials[code])
            combo.setToolTip(f"Select uniaxial material for response code {code}")
            materials_layout.addWidget(code_label, row, 0)
            materials_layout.addWidget(combo, row, 1)
            self.material_combos[code] = combo
        left_layout.addWidget(materials_group)
        # Base section group (optional)
        base_section_group = QGroupBox("Base Section (Optional)")
        base_section_layout = QFormLayout(base_section_group)
        self.base_section_combo = QComboBox()
        self.base_section_combo.addItem("None", None)
        for tag, s in Section.get_all_sections().items():
            self.base_section_combo.addItem(f"{s.user_name} (Tag: {tag})", s)
        if hasattr(section, 'base_section') and section.base_section:
            set_combo_to_material(self.base_section_combo, section.base_section)
        base_section_layout.addRow("Base Section:", self.base_section_combo)
        left_layout.addWidget(base_section_group)
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
            materials = {}
            for code, combo in self.material_combos.items():
                material = get_material_by_combo_selection(combo)
                if material:
                    materials[code] = material
            if not materials:
                QMessageBox.warning(self, "Input Error", "Please select at least one material for a response code.")
                return
            base_section = self.base_section_combo.currentData()
            update_values = {"materials": materials}
            if base_section:
                update_values["base_section"] = base_section
            self.section.materials = materials
            if base_section:
                self.section.base_section = base_section
            QMessageBox.information(self, "Success", f"Section '{self.section.user_name}' updated successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update section: {str(e)}")


if __name__ == "__main__":
    from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial, ElasticIsotropicMaterial
    from qtpy.QtWidgets import QApplication
    elas1 = ElasticUniaxialMaterial(user_name="Elastic1", E=30000, G=12000, nu=0.2)
    elas2 = ElasticUniaxialMaterial(user_name="Elastic2", E=25000, G=10000, nu=0.3)
    elas3 = ElasticIsotropicMaterial(user_name="Elastic3", E=20000, G=8000, nu=0.25)
    app = QApplication([])
    dialog = AggregatorSectionCreationDialog()
    if dialog.exec_() == QDialog.Accepted:
        print("Section created:", dialog.created_section)
    else:
        print("Creation cancelled")
    


    
    app.exec_()
