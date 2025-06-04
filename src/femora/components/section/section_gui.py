"""
Section GUI components for FEMORA
Following the established patterns from material and element GUIs
"""

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
    QDialog, QFormLayout, QMessageBox, QHeaderView, QGridLayout,
    QMenu, QTextEdit, QTabWidget, QGroupBox, QFrame
)

from femora.components.section.section_base import Section, SectionRegistry
from femora.components.section.section_opensees import *
from femora.components.Material.materialBase import Material


class SectionManagerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Section type selection
        type_layout = QGridLayout()
        
        # Section type dropdown
        self.section_type_combo = QComboBox()
        self.section_type_combo.addItems(SectionRegistry.get_section_types())
        
        create_section_btn = QPushButton("Create New Section")
        create_section_btn.clicked.connect(self.open_section_creation_dialog)
        
        type_layout.addWidget(QLabel("Section Type:"), 0, 0)
        type_layout.addWidget(self.section_type_combo, 0, 1)
        type_layout.addWidget(create_section_btn, 1, 0, 1, 2)
        
        layout.addLayout(type_layout)
        
        # Sections table
        self.sections_table = QTableWidget()
        self.sections_table.setColumnCount(6)  # Tag, Type, Name, Materials, Edit, Delete
        self.sections_table.setHorizontalHeaderLabels(["Tag", "Type", "Name", "Materials", "Edit", "Delete"])
        header = self.sections_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        # Enable context menu (right-click menu)
        self.sections_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sections_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Select full rows when clicking
        self.sections_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sections_table.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addWidget(self.sections_table)
        
        # Button layout for actions
        button_layout = QHBoxLayout()
        
        # Refresh sections button
        refresh_btn = QPushButton("Refresh Sections List")
        refresh_btn.clicked.connect(self.refresh_sections_list)
        button_layout.addWidget(refresh_btn)
        
        # Clear all sections button
        clear_all_btn = QPushButton("Clear All Sections")
        clear_all_btn.clicked.connect(self.clear_all_sections)
        button_layout.addWidget(clear_all_btn)
        
        layout.addLayout(button_layout)
        
        # Initial refresh
        self.refresh_sections_list()

    def open_section_creation_dialog(self):
        """Open dialog to create a new section of selected type"""
        section_type = self.section_type_combo.currentText()
        
        dialog = SectionCreationDialog(section_type, self)
        
        # Only refresh if a section was actually created
        if dialog.exec() == QDialog.Accepted and hasattr(dialog, 'created_section'):
            self.refresh_sections_list()

    def refresh_sections_list(self):
        """Update the sections table with current sections"""
        # Clear existing rows
        self.sections_table.setRowCount(0)
        
        # Get all sections
        sections = Section.get_all_sections()
        
        # Set row count
        self.sections_table.setRowCount(len(sections))
        
        # Populate table
        for row, (tag, section) in enumerate(sections.items()):
            # Tag
            tag_item = QTableWidgetItem(str(tag))
            tag_item.setFlags(tag_item.flags() & ~Qt.ItemIsEditable)
            self.sections_table.setItem(row, 0, tag_item)
            
            # Section Type
            type_item = QTableWidgetItem(section.section_name)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.sections_table.setItem(row, 1, type_item)
            
            # User Name
            name_item = QTableWidgetItem(section.user_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.sections_table.setItem(row, 2, name_item)
            
            # Materials used
            materials = section.get_materials()
            materials_str = ", ".join([mat.user_name for mat in materials]) if materials else "None"
            materials_item = QTableWidgetItem(materials_str)
            materials_item.setFlags(materials_item.flags() & ~Qt.ItemIsEditable)
            self.sections_table.setItem(row, 3, materials_item)
            
            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, sec=section: self.open_section_edit_dialog(sec))
            self.sections_table.setCellWidget(row, 4, edit_btn)

            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, tag=tag: self.delete_section(tag))
            self.sections_table.setCellWidget(row, 5, delete_btn)

    def show_context_menu(self, position):
        """Show context menu for sections table"""
        menu = QMenu()
        view_action = menu.addAction("View TCL")
        edit_action = menu.addAction("Edit Section")
        delete_action = menu.addAction("Delete Section")
        
        action = menu.exec_(self.sections_table.viewport().mapToGlobal(position))
        
        if action == view_action:
            selected_row = self.sections_table.currentRow()
            if selected_row != -1:
                tag = int(self.sections_table.item(selected_row, 0).text())
                section = Section.get_section_by_tag(tag)
                self.show_section_tcl(section)
        elif action == edit_action:
            selected_row = self.sections_table.currentRow()
            if selected_row != -1:
                tag = int(self.sections_table.item(selected_row, 0).text())
                section = Section.get_section_by_tag(tag)
                self.open_section_edit_dialog(section)
        elif action == delete_action:
            selected_row = self.sections_table.currentRow()
            if selected_row != -1:
                tag = int(self.sections_table.item(selected_row, 0).text())
                self.delete_section(tag)

    def show_section_tcl(self, section):
        """Show the TCL representation of a section"""
        tcl_dialog = QDialog(self)
        tcl_dialog.setWindowTitle(f"TCL for {section.user_name}")
        tcl_dialog.setGeometry(400, 300, 600, 200)
        
        layout = QVBoxLayout(tcl_dialog)
        
        tcl_text = QTextEdit()
        tcl_text.setPlainText(section.to_tcl())
        tcl_text.setReadOnly(True)
        layout.addWidget(tcl_text)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(tcl_dialog.accept)
        layout.addWidget(close_btn)
        
        tcl_dialog.exec()

    def open_section_edit_dialog(self, section):
        """Open dialog to edit an existing section"""
        dialog = SectionEditDialog(section, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_sections_list()

    def delete_section(self, tag):
        """Delete a section from the system"""
        # Confirm deletion
        reply = QMessageBox.question(self, 'Delete Section', 
                                     f"Are you sure you want to delete section with tag {tag}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            Section.delete_section(tag)
            self.refresh_sections_list()

    def clear_all_sections(self):
        """Clear all sections from the system"""
        reply = QMessageBox.question(self, 'Clear All Sections', 
                                     "Are you sure you want to delete all sections?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            Section.clear_all_sections()
            self.refresh_sections_list()


class SectionCreationDialog(QDialog):
    def __init__(self, section_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Create {section_type} Section")
        self.section_type = section_type

        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        
        # Left side - Parameters
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Get the section class
        self.section_class = SectionRegistry._section_types[section_type]

        # User-specified Name
        name_group = QGroupBox("Section Information")
        name_layout = QFormLayout(name_group)
        self.user_name_input = QLineEdit()
        name_layout.addRow("Section Name:", self.user_name_input)
        left_layout.addWidget(name_group)

        # Create parameters group
        params_group = QGroupBox("Section Parameters")
        params_layout = QGridLayout(params_group)
        
        # Parameter inputs
        self.param_inputs = {}
        parameters = self.section_class.get_parameters()
        descriptions = self.section_class.get_description()

        # Handle different section types
        if section_type == "Elastic":
            self._create_elastic_section_inputs(params_layout, parameters, descriptions)
        elif section_type == "Aggregator":
            self._create_aggregator_section_inputs(params_layout)
        elif section_type == "Uniaxial":
            self._create_uniaxial_section_inputs(params_layout)
        elif section_type == "Fiber":
            self._create_fiber_section_inputs(params_layout)
        else:
            # Generic parameter creation
            self._create_generic_inputs(params_layout, parameters, descriptions)

        left_layout.addWidget(params_group)

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

        # Add left widget to main layout
        main_layout.addWidget(left_widget)

        # Vertical line separator
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # Right side - Notes/Help
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        notes_display = QTextEdit()
        notes_display.setHtml(self._get_section_help(section_type))
        notes_display.setReadOnly(True)
        right_layout.addWidget(notes_display)
        
        main_layout.addWidget(right_widget)
        
        # Set layout proportions
        main_layout.setStretch(0, 3)
        main_layout.setStretch(2, 2)

    def _create_elastic_section_inputs(self, layout, parameters, descriptions):
        """Create inputs specific to Elastic sections"""
        row = 0
        for param, desc in zip(parameters, descriptions):
            label = QLabel(param)
            input_field = QLineEdit()
            desc_label = QLabel(f"({desc})")
            
            layout.addWidget(label, row, 0)
            layout.addWidget(input_field, row, 1)
            layout.addWidget(desc_label, row, 2)
            
            self.param_inputs[param] = input_field
            row += 1

    def _create_aggregator_section_inputs(self, layout):
        """Create inputs specific to Aggregator sections"""
        # Material selection for different response codes
        self.material_combo = QComboBox()
        self.refresh_materials()
        
        self.response_code_combo = QComboBox()
        self.response_code_combo.addItems(['P', 'Mz', 'My', 'Vy', 'Vz', 'T'])
        
        add_material_btn = QPushButton("Add Material")
        add_material_btn.clicked.connect(self.add_material_to_aggregator)
        
        layout.addWidget(QLabel("Material:"), 0, 0)
        layout.addWidget(self.material_combo, 0, 1)
        layout.addWidget(QLabel("Response Code:"), 1, 0)
        layout.addWidget(self.response_code_combo, 1, 1)
        layout.addWidget(add_material_btn, 2, 0, 1, 2)
        
        # List of added materials
        self.materials_list = QTextEdit()
        self.materials_list.setMaximumHeight(100)
        self.materials_list.setReadOnly(True)
        layout.addWidget(QLabel("Added Materials:"), 3, 0)
        layout.addWidget(self.materials_list, 4, 0, 1, 2)
        
        self.aggregator_materials = {}

    def _create_uniaxial_section_inputs(self, layout):
        """Create inputs specific to Uniaxial sections"""
        # Material selection
        self.material_combo = QComboBox()
        self.refresh_materials()
        
        # Response code selection
        self.response_code_combo = QComboBox()
        self.response_code_combo.addItems(['P', 'Mz', 'My', 'Vy', 'Vz', 'T'])
        
        layout.addWidget(QLabel("Material:"), 0, 0)
        layout.addWidget(self.material_combo, 0, 1)
        layout.addWidget(QLabel("Response Code:"), 1, 0)
        layout.addWidget(self.response_code_combo, 1, 1)

    def _create_fiber_section_inputs(self, layout):
        """Create inputs specific to Fiber sections"""
        # Fiber sections are complex and need specialized dialog
        info_label = QLabel("Fiber sections are complex and require a specialized interface.\n"
                           "Click 'Use Fiber Dialog' to open the dedicated fiber section creator.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label, 0, 0, 1, 2)
        
        self.fiber_dialog_btn = QPushButton("Use Fiber Dialog")
        self.fiber_dialog_btn.clicked.connect(self.open_fiber_dialog)
        layout.addWidget(self.fiber_dialog_btn, 1, 0, 1, 2)
        
        self.created_fiber_section = None

    def _create_generic_inputs(self, layout, parameters, descriptions):
        """Create generic parameter inputs"""
        row = 0
        for param, desc in zip(parameters, descriptions):
            label = QLabel(param)
            input_field = QLineEdit()
            desc_label = QLabel(f"({desc})")
            
            layout.addWidget(label, row, 0)
            layout.addWidget(input_field, row, 1)
            layout.addWidget(desc_label, row, 2)
            
            self.param_inputs[param] = input_field
            row += 1

    def refresh_materials(self):
        """Refresh the materials combo box"""
        self.material_combo.clear()
        self.material_combo.addItem("Select Material", None)
        for tag, material in Material.get_all_materials().items():
            self.material_combo.addItem(f"{material.user_name} (Tag: {tag})", material)

    def add_material_to_aggregator(self):
        """Add a material to the aggregator section"""
        material = self.material_combo.currentData()
        response_code = self.response_code_combo.currentText()
        
        if material is None:
            QMessageBox.warning(self, "Error", "Please select a material")
            return
        
        if response_code in self.aggregator_materials:
            reply = QMessageBox.question(self, "Replace Material", 
                                        f"Response code {response_code} already has a material. Replace it?")
            if reply != QMessageBox.Yes:
                return
        
        self.aggregator_materials[response_code] = material
        self._update_materials_list()

    def _update_materials_list(self):
        """Update the materials list display"""
        text = ""
        for code, material in self.aggregator_materials.items():
            text += f"{code}: {material.user_name}\n"
        self.materials_list.setPlainText(text)

    def _get_section_help(self, section_type):
        """Get help text for the section type"""
        help_texts = {
            "Elastic": """
            <b>Elastic Section</b><br>
            Creates a linear elastic section with constant properties.<br><br>
            <b>Required Parameters:</b><br>
            • E: Young's modulus<br>
            • A: Cross-sectional area<br>
            • Iz: Moment of inertia about z-axis<br><br>
            <b>Optional Parameters:</b><br>
            • Iy: Moment of inertia about y-axis (3D)<br>
            • G: Shear modulus<br>
            • J: Torsional constant
            """,
            "Fiber": """
            <b>Fiber Section</b><br>
            Creates a section using fiber discretization for nonlinear analysis.<br><br>
            Fibers are added programmatically using the add_fiber() method.<br>
            Each fiber has coordinates, area, and a material.
            """,
            "Aggregator": """
            <b>Aggregator Section</b><br>
            Combines different uniaxial materials for different response quantities.<br><br>
            <b>Response Codes:</b><br>
            • P: Axial force<br>
            • Mz: Moment about z-axis<br>
            • My: Moment about y-axis<br>
            • Vy: Shear force in y-direction<br>
            • Vz: Shear force in z-direction<br>
            • T: Torsion
            """,
            "Uniaxial": """
            <b>Uniaxial Section</b><br>
            Uses a single uniaxial material for one response quantity.<br><br>
            Specify the material and the response code it represents.
            """
        }
        return help_texts.get(section_type, "<b>Section Help</b><br>No specific help available.")

    def open_fiber_dialog(self):
        """Open the specialized fiber section dialog"""
        from femora.components.section.section_fiber_gui import create_fiber_section_dialog
        fiber_section = create_fiber_section_dialog(parent=self)
        if fiber_section:
            self.created_fiber_section = fiber_section
            QMessageBox.information(self, "Success", f"Fiber section '{fiber_section.user_name}' created successfully!")

    def create_section(self):
        try:
            # Validate user name
            user_name = self.user_name_input.text().strip()
            if not user_name:
                QMessageBox.warning(self, "Input Error", "Please enter a section name.")
                return
            
            if user_name in Section._names:
                QMessageBox.warning(self, "Input Error", f"Section with name {user_name} already exists.")
                return

            # Collect parameters based on section type
            if self.section_type == "Elastic":
                params = {}
                for param, input_field in self.param_inputs.items():
                    value = input_field.text().strip()
                    if value:
                        params[param] = value
                
                if not params:
                    QMessageBox.warning(self, "Input Error", "Please enter at least the required parameters (E, A, Iz).")
                    return

                # Create section
                self.created_section = SectionRegistry.create_section(
                    section_type=self.section_type,
                    user_name=user_name,
                    **params
                )
                
            elif self.section_type == "Aggregator":
                if not self.aggregator_materials:
                    QMessageBox.warning(self, "Input Error", "Please add at least one material to the aggregator.")
                    return
                
                self.created_section = SectionRegistry.create_section(
                    section_type=self.section_type,
                    user_name=user_name,
                    materials=self.aggregator_materials
                )
                
            elif self.section_type == "Uniaxial":
                material = self.material_combo.currentData()
                response_code = self.response_code_combo.currentText()
                
                if material is None:
                    QMessageBox.warning(self, "Input Error", "Please select a material.")
                    return
                
                self.created_section = SectionRegistry.create_section(
                    section_type=self.section_type,
                    user_name=user_name,
                    material=material,
                    response_code=response_code
                )
                
            elif self.section_type == "Fiber":
                if not self.created_fiber_section:
                    QMessageBox.warning(self, "Input Error", "Please create a fiber section using the Fiber Dialog.")
                    return
                
                # Update the fiber section name to match user input
                self.created_fiber_section.user_name = user_name
                self.created_section = self.created_fiber_section
            
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class SectionEditDialog(QDialog):
    def __init__(self, section, parent=None):
        super().__init__(parent)
        self.section = section
        self.setWindowTitle(f"Edit {section.section_name} Section (Tag: {section.tag})")

        layout = QVBoxLayout(self)
        
        # Read-only information
        info_group = QGroupBox("Section Information")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("Tag:", QLabel(str(section.tag)))
        info_layout.addRow("Type:", QLabel(section.section_name))
        
        # User name (editable)
        self.user_name_input = QLineEdit(section.user_name)
        info_layout.addRow("Name:", self.user_name_input)
        
        layout.addWidget(info_group)
        
        # Parameters (if applicable)
        if hasattr(section, 'params') and section.params:
            params_group = QGroupBox("Parameters")
            params_layout = QGridLayout(params_group)
            
            self.param_inputs = {}
            row = 0
            for param, value in section.params.items():
                label = QLabel(param)
                input_field = QLineEdit(str(value))
                
                params_layout.addWidget(label, row, 0)
                params_layout.addWidget(input_field, row, 1)
                
                self.param_inputs[param] = input_field
                row += 1
            
            layout.addWidget(params_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_changes(self):
        try:
            # Update user name
            new_name = self.user_name_input.text().strip()
            if new_name != self.section.user_name:
                if new_name in Section._names:
                    QMessageBox.warning(self, "Input Error", f"Section with name {new_name} already exists.")
                    return
                
                # Update name tracking
                Section._names.pop(self.section.user_name)
                Section._names[new_name] = self.section
                self.section.user_name = new_name
            
            # Update parameters if they exist
            if hasattr(self, 'param_inputs'):
                new_values = {}
                for param, input_field in self.param_inputs.items():
                    value = input_field.text().strip()
                    if value:
                        new_values[param] = value
                
                if new_values:
                    self.section.update_values(new_values)
            
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    import sys
    from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial, ElasticUniaxialMaterial

    # Create the Qt Application
    app = QApplication(sys.argv)
    
    # Create some test materials
    mat1 = ElasticIsotropicMaterial(user_name="Steel0", E=200e3, nu=0.3, rho=7.85e-9)
    mat2 = ElasticUniaxialMaterial(user_name="Steel_Uniaxial0", E=200e3)
    
    # Add some initial sections for testing
    from femora.components.section.section_base import SectionRegistry

    # Elastic section
    SectionRegistry.create_section(
        section_type="Elastic",
        user_name="ElasticSection1",
        E=200e3,
        A=1000,
        Iz=5000
    )

    # Uniaxial section
    SectionRegistry.create_section(
        section_type="Uniaxial",
        user_name="UniaxialSection1",
        material=mat2,
        response_code="P"
    )

    # Aggregator section
    SectionRegistry.create_section(
        section_type="Aggregator",
        user_name="AggregatorSection1",
        materials={"P": mat2, "Mz": mat2}
    )


    steel = ElasticUniaxialMaterial(user_name="Steel1", E=200000, eta=0.0)
    concrete = ElasticUniaxialMaterial(user_name="Concrete1", E=30000, eta=0.0)
    
    # Create fiber section
    section = FiberSection("Example_Section", GJ=1000000)
    
    # Add rectangular concrete patch
    section.add_rectangular_patch(concrete, 10, 10, -0.15, -0.25, 0.15, 0.25)
    
    # Add steel reinforcement layers
    section.add_straight_layer(steel, 4, 0.0005, -0.12, -0.22, 0.12, -0.22)  # Bottom
    section.add_straight_layer(steel, 4, 0.0005, -0.12, 0.22, 0.12, 0.22)    # Top
    section.add_straight_layer(steel, 3, 0.0005, -0.12, -0.1, -0.12, 0.1)    # Left
    section.add_straight_layer(steel, 3, 0.0005, 0.12, -0.1, 0.12, 0.1)      # Right
    

    section.add_fiber(0.0, 0.0, 0.0001, steel)  # Central fiber

    # Create and show the SectionManagerTab
    section_manager = SectionManagerTab()
    section_manager.show()
    
    sys.exit(app.exec_())