"""
Isolator2Spring Section GUI Dialogs
Implements creation and edit dialogs for Isolator2SpringSection
"""
from qtpy.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFormLayout
from femora.components.section.section_opensees import Isolator2SpringSection

class Isolator2SpringSectionCreationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Isolator2Spring Section")
        self.created_section = None
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.inputs = {}
        # Parameter fields
        params = Isolator2SpringSection.get_parameters()
        descs = Isolator2SpringSection.get_description()
        for param, desc in zip(params, descs):
            le = QLineEdit()
            le.setPlaceholderText(desc)
            form.addRow(f"{param}", le)
            self.inputs[param] = le
        layout.addLayout(form)
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Section name")
        layout.addWidget(QLabel("Section Name:"))
        layout.addWidget(self.name_edit)
        # Buttons
        btns = QHBoxLayout()
        ok_btn = QPushButton("Create")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
    def accept(self):
        # Validate and create section
        try:
            values = {k: float(self.inputs[k].text()) for k in self.inputs}
            name = self.name_edit.text().strip() or "Unnamed"
            self.created_section = Isolator2SpringSection(user_name=name, **values)
            super().accept()
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

class Isolator2SpringSectionEditDialog(QDialog):
    def __init__(self, section, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Isolator2Spring Section: {section.user_name}")
        self.section = section
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.inputs = {}
        params = Isolator2SpringSection.get_parameters()
        descs = Isolator2SpringSection.get_description()
        values = section.get_values(params)
        for param, desc in zip(params, descs):
            le = QLineEdit(str(values.get(param, "")))
            le.setPlaceholderText(desc)
            form.addRow(f"{param}", le)
            self.inputs[param] = le
        layout.addLayout(form)
        # Name field
        self.name_edit = QLineEdit(section.user_name)
        layout.addWidget(QLabel("Section Name:"))
        layout.addWidget(self.name_edit)
        # Buttons
        btns = QHBoxLayout()
        ok_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
    def accept(self):
        try:
            values = {k: float(self.inputs[k].text()) for k in self.inputs}
            self.section.update_values(values)
            self.section.user_name = self.name_edit.text().strip() or self.section.user_name
            super().accept()
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))
