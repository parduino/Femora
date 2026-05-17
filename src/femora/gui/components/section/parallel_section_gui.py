"""
Parallel Section GUI Dialogs
Uses ParallelSection class methods instead of hardcoding
"""

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QFormLayout, QMessageBox, QGridLayout, QFrame, QTextBrowser, QGroupBox, QWidget, QListWidget, QListWidgetItem
)
from qtpy.QtCore import Qt

from femora.components.section.section_opensees import ParallelSection
from femora.components.section.section_base import Section

class ParallelSectionCreationDialog(QDialog):
    """
    Dialog for creating new ParallelSection sections using class methods
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Parallel Section")
        self.setMinimumSize(600, 400)
        
        self.parameters = ParallelSection.get_parameters()
        self.descriptions = ParallelSection.get_description()
        
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
        
        # Sections group
        sections_group = QGroupBox("Sections to Combine in Parallel")
        sections_layout = QVBoxLayout(sections_group)
        self.sections_list = QListWidget()
        self.sections_list.setSelectionMode(QListWidget.MultiSelection)
        for tag, section in Section.get_all_sections().items():
            item = QListWidgetItem(f"{section.user_name} (Tag: {tag})")
            item.setData(Qt.UserRole, section)
            self.sections_list.addItem(item)
        sections_layout.addWidget(self.sections_list)
        left_layout.addWidget(sections_group)
        
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
        help_display.setHtml(ParallelSection.get_help_text())
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
                existing_section = ParallelSection.get_section_by_name(user_name)
                QMessageBox.warning(self, "Input Error", f"Section with name '{user_name}' already exists.")
                return
            except KeyError:
                pass
            selected_items = self.sections_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Input Error", "Please select at least one section to combine.")
                return
            sections = [item.data(Qt.UserRole) for item in selected_items]
            params = {'sections': sections}
            try:
                validated_params = ParallelSection.validate_section_parameters(**params)
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
                return
            self.created_section = ParallelSection(user_name=user_name, **params)
            QMessageBox.information(self, "Success", f"Parallel Section '{user_name}' created successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create section: {str(e)}")

class ParallelSectionEditDialog(QDialog):
    """
    Dialog for editing existing ParallelSection sections using class methods
    """
    def __init__(self, section, parent=None):
        super().__init__(parent)
        self.section = section
        self.setWindowTitle(f"Edit Parallel Section: {section.user_name}")
        self.setMinimumSize(600, 400)
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
        # Sections group
        sections_group = QGroupBox("Sections to Combine in Parallel")
        sections_layout = QVBoxLayout(sections_group)
        self.sections_list = QListWidget()
        self.sections_list.setSelectionMode(QListWidget.MultiSelection)
        all_sections = list(Section.get_all_sections().values())
        for s in all_sections:
            item = QListWidgetItem(f"{s.user_name} (Tag: {s.tag})")
            item.setData(Qt.UserRole, s)
            self.sections_list.addItem(item)
            if s in section.sections:
                item.setSelected(True)
        sections_layout.addWidget(self.sections_list)
        left_layout.addWidget(sections_group)
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
            selected_items = self.sections_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Input Error", "Please select at least one section to combine.")
                return
            sections = [item.data(Qt.UserRole) for item in selected_items]
            self.section.sections = sections
            QMessageBox.information(self, "Success", f"Section '{self.section.user_name}' updated successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update section: {str(e)}")
