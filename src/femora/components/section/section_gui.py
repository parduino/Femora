"""
Main Section GUI Manager
Uses separate dialog files for each section type
"""

from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
    QDialog, QMessageBox, QHeaderView, QGridLayout, QMenu
)
from qtpy.QtCore import Qt

from femora.components.section.section_base import Section, SectionRegistry, SectionManager
from femora.components.section.section_opensees import *

# Import separate dialog files for each section type

from femora.components.section.elastic_section_gui import ElasticSectionCreationDialog, ElasticSectionEditDialog
from femora.components.section.wf2d_section_gui import WFSection2dCreationDialog, WFSection2dEditDialog
from femora.components.section.rc_section_gui import RCSectionCreationDialog, RCSectionEditDialog
from femora.components.section.wf2d_section_gui import WFSection2dCreationDialog, WFSection2dEditDialog
from femora.components.section.elastic_membrane_section_gui import ElasticMembranePlateSectionCreationDialog, ElasticMembranePlateSectionEditDialog
from femora.components.section.platefiber_section_gui import PlateFiberSectionCreationDialog, PlateFiberSectionEditDialog
from femora.components.section.aggregator_section_gui import AggregatorSectionCreationDialog, AggregatorSectionEditDialog
from femora.components.section.uniaxial_section_gui import UniaxialSectionCreationDialog, UniaxialSectionEditDialog
from femora.components.section.parallel_section_gui import ParallelSectionCreationDialog, ParallelSectionEditDialog
from femora.components.section.bidirectional_section_gui import BidirectionalSectionCreationDialog, BidirectionalSectionEditDialog
from femora.components.section.isolator2spring_section_gui import Isolator2SpringSectionCreationDialog, Isolator2SpringSectionEditDialog


class SectionManagerTab(QWidget):
    """
    Main Section Manager Tab with support for different section types
    Uses separate dialog files for each section type
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Section type selection and creation
        type_layout = QGridLayout()
        
        self.section_type_combo = QComboBox()
        # Get available section types
        available_types = SectionRegistry.get_section_types()
        self.section_type_combo.addItems(available_types)
        
        create_section_btn = QPushButton("Create New Section")
        create_section_btn.clicked.connect(self.open_section_creation_dialog)
        
        type_layout.addWidget(QLabel("Section Type:"), 0, 0)
        type_layout.addWidget(self.section_type_combo, 0, 1)
        type_layout.addWidget(create_section_btn, 1, 0, 1, 2)
        
        layout.addLayout(type_layout)
        
        # Sections table
        self.sections_table = QTableWidget()
        self.sections_table.setColumnCount(4)  # Type, Name, Edit, Delete
        self.sections_table.setHorizontalHeaderLabels(["Type", "Name", "Edit", "Delete"])
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
        """
        Open the appropriate creation dialog based on section type
        """
        section_type = self.section_type_combo.currentText()
        
        if section_type == "Elastic":
            dialog = ElasticSectionCreationDialog(self)
        elif section_type == "WFSection2d":
            dialog = WFSection2dCreationDialog(self)
        elif section_type == "RC":
            dialog = RCSectionCreationDialog(self)
        elif section_type == "ElasticMembranePlateSection":
            dialog = ElasticMembranePlateSectionCreationDialog(self)
        elif section_type == "PlateFiber":
            dialog = PlateFiberSectionCreationDialog(self)
        elif section_type == "Fiber":
            QMessageBox.information(self, "Not Available", "Fiber section GUI will be implemented in the future.")
            return
        elif section_type == "Aggregator":
            dialog = AggregatorSectionCreationDialog(self)
        elif section_type == "Uniaxial":
            dialog = UniaxialSectionCreationDialog(self)
        elif section_type == "Parallel":
            dialog = ParallelSectionCreationDialog(self)
        elif section_type == "Bidirectional":
            dialog = BidirectionalSectionCreationDialog(self)
        elif section_type == "Isolator2spring":
            dialog = Isolator2SpringSectionCreationDialog(self)
        else:
            QMessageBox.warning(self, "Error", f"No dialog available for section type: {section_type}")
            return
        
        # Execute dialog and refresh if section was created
        if dialog.exec() == QDialog.Accepted and hasattr(dialog, 'created_section'):
            self.refresh_sections_list()

    def open_section_edit_dialog(self, section):
        """
        Open the appropriate edit dialog based on section type
        """
        section_type = section.section_name
        
        if section_type == "Elastic":
            dialog = ElasticSectionEditDialog(section, self)
        elif section_type == "WFSection2d":
            dialog = WFSection2dEditDialog(section, self)
        elif section_type == "RC":
            dialog = RCSectionEditDialog(section, self)
        elif section_type == "ElasticMembranePlateSection":
            dialog = ElasticMembranePlateSectionEditDialog(section, self)
        elif section_type == "PlateFiber":
            dialog = PlateFiberSectionEditDialog(section, self)
        elif section_type == "Fiber":
            QMessageBox.information(self, "Not Available", "Fiber section editing will be implemented in the future.")
            return
        elif section_type == "Aggregator":
            dialog = AggregatorSectionEditDialog(section, self)
        elif section_type == "Uniaxial":
            dialog = UniaxialSectionEditDialog(section, self)
        elif section_type == "Parallel":
            dialog = ParallelSectionEditDialog(section, self)
        elif section_type == "Bidirectional":
            dialog = BidirectionalSectionEditDialog(section, self)
        elif section_type == "Isolator2spring":
            dialog = Isolator2SpringSectionEditDialog(section, self)
        else:
            QMessageBox.warning(self, "Error", f"No edit dialog available for section type: {section_type}")
            return
        
        # Execute dialog and refresh if changes were made
        if dialog.exec() == QDialog.Accepted:
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
            # Section Type
            type_item = QTableWidgetItem(section.section_name)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.sections_table.setItem(row, 0, type_item)
            
            # User Name
            name_item = QTableWidgetItem(section.user_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.sections_table.setItem(row, 1, name_item)
            
            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, sect=section: self.open_section_edit_dialog(sect))
            self.sections_table.setCellWidget(row, 2, edit_btn)

            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, tag=tag: self.delete_section(tag))
            self.sections_table.setCellWidget(row, 3, delete_btn)

    def show_context_menu(self, position):
        """Show context menu for sections table"""
        menu = QMenu()
        edit_action = menu.addAction("Edit Section")
        delete_action = menu.addAction("Delete Section")
        
        action = menu.exec_(self.sections_table.viewport().mapToGlobal(position))
        
        if action == edit_action:
            selected_row = self.sections_table.currentRow()
            if selected_row != -1:
                name = self.sections_table.item(selected_row, 1).text()
                # Find section by user_name
                section = next((s for s in Section.get_all_sections().values() if s.user_name == name), None)
                if section:
                    self.open_section_edit_dialog(section)
        elif action == delete_action:
            selected_row = self.sections_table.currentRow()
            if selected_row != -1:
                name = self.sections_table.item(selected_row, 1).text()
                section = next((s for s in Section.get_all_sections().values() if s.user_name == name), None)
                if section:
                    self.delete_section(section.tag)

    def delete_section(self, tag):
        """Delete a section from the system"""
        section = Section.get_section_by_tag(tag)
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 'Delete Section', 
            f"Are you sure you want to delete section '{section.user_name}' (Tag: {tag})?\n\n"
            f"This action cannot be undone and may affect elements using this section.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            Section.delete_section(tag)
            self.refresh_sections_list()
            QMessageBox.information(self, "Success", f"Section '{section.user_name}' deleted successfully.")

    def clear_all_sections(self):
        """Clear all sections from the system"""
        if not Section.get_all_sections():
            QMessageBox.information(self, "No Sections", "There are no sections to clear.")
            return
            
        reply = QMessageBox.question(
            self, 'Clear All Sections', 
            "Are you sure you want to delete ALL sections?\n\n"
            "This action cannot be undone and may affect elements using these sections.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            count = len(Section.get_all_sections())
            Section.clear_all_sections()
            self.refresh_sections_list()
            QMessageBox.information(self, "Success", f"All {count} sections cleared successfully.")


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    import sys
    from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial, ElasticIsotropicMaterial
    from femora.components.section.section_opensees import ElasticSection
    from femora.components.section.section_opensees import WFSection2d
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    
    # Create some test materials (if needed for future section types)
    steel = ElasticUniaxialMaterial(user_name="Steel", E=200000, eta=0.0)
    concrete = ElasticUniaxialMaterial(user_name="Concrete", E=30000, eta=0.0)

    steelND = ElasticIsotropicMaterial(user_name="SteelND Isotropic", E=200000, nu=0.3)

    # Add an Elastic section
    elastic_section = ElasticSection(
        user_name="Elastic Beam",
        E=200000,
        A=0.02,
        Iz=8.1e-6
    )

    # Add a WFSection2d section
    wf_section = WFSection2d(
        user_name="W-Shape",
        material="Steel",
        d=0.3,
        tw=0.01,
        bf=0.15,
        tf=0.02,
        E=200000,
        Nflweb=10,
        Nflflange=10,
    )
    
    # Create and show the SectionManagerTab
    section_manager_tab = SectionManagerTab()
    section_manager_tab.show()

    sys.exit(app.exec())