from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QMessageBox, QMenu,
    QListWidget, QListWidgetItem, QLineEdit, QCheckBox, QGridLayout
)
from qtpy.QtCore import Qt

from femora.components.interface.interface_base import InterfaceBase
from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface  # Ensure class is imported
from femora.components.interface.embedded_interface_gui import (
    EmbeddedInterfaceCreationDialog,
    EmbeddedInterfaceEditDialog,
)


class _InterfaceTypeRegistry:
    """Registry mapping *interface type name* → class."""

    _types = {
        "EmbeddedBeamSolidInterface": EmbeddedBeamSolidInterface,
    }

    @classmethod
    def types(cls):
        return list(cls._types.keys())

    @classmethod
    def get(cls, type_name: str):
        return cls._types[type_name]


class InterfaceManagerTab(QWidget):
    """Main tab for creating, listing and managing Interface objects."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._build_ui()
        self.refresh_interface_list()

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        # ------------------------------------------------------------------
        # Section: interface type selection & creation
        # ------------------------------------------------------------------
        selector_layout = QVBoxLayout()

        # Interface type selector
        self.type_combo = QComboBox()
        self.type_combo.addItems(_InterfaceTypeRegistry.types())

        create_btn = QPushButton("Create New Interface")
        create_btn.clicked.connect(self._open_creation_dialog)

        interface_type_layout = QHBoxLayout()
        interface_type_layout.addWidget(QLabel("Interface Type:"))
        interface_type_layout.addWidget(self.type_combo)
        selector_layout.addLayout(interface_type_layout)
        selector_layout.addWidget(create_btn)

        main_layout.addLayout(selector_layout)

        # ------------------------------------------------------------------
        # Table of existing interfaces
        # ------------------------------------------------------------------
        self.interface_table = QTableWidget()
        self.interface_table.setColumnCount(3)
        self.interface_table.setHorizontalHeaderLabels(["Name", "Type", "Owners"])
        header = self.interface_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # right-click menu
        self.interface_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.interface_table.customContextMenuRequested.connect(self._show_context_menu)
        self.interface_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.interface_table.setSelectionMode(QTableWidget.SingleSelection)

        main_layout.addWidget(self.interface_table)

        # ------------------------------------------------------------------
        # Action buttons
        # ------------------------------------------------------------------
        action_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_interface_list)
        clear_btn = QPushButton("Clear All Interfaces")
        clear_btn.clicked.connect(self._clear_all_interfaces)

        action_layout.addWidget(refresh_btn)
        action_layout.addWidget(clear_btn)
        main_layout.addLayout(action_layout)

    # ------------------------------------------------------------------
    # Populate / refresh table
    # ------------------------------------------------------------------
    def refresh_interface_list(self):
        interfaces = InterfaceBase.all()
        self.interface_table.setRowCount(0)
        self.interface_table.setRowCount(len(interfaces))
        for row, (name, iface) in enumerate(interfaces.items()):
            # Name – not editable
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.interface_table.setItem(row, 0, name_item)

            # Type
            type_item = QTableWidgetItem(iface.__class__.__name__)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.interface_table.setItem(row, 1, type_item)

            # Owners (comma-separated)
            owners_item = QTableWidgetItem(", ".join(iface.owners))
            owners_item.setFlags(owners_item.flags() & ~Qt.ItemIsEditable)
            self.interface_table.setItem(row, 2, owners_item)

    # ------------------------------------------------------------------
    # Creation dialog launcher (interface-specific)
    # ------------------------------------------------------------------
    def _open_creation_dialog(self):
        type_name = self.type_combo.currentText()
        iface_cls = _InterfaceTypeRegistry.get(type_name)

        if iface_cls == EmbeddedBeamSolidInterface:
            dialog = EmbeddedInterfaceCreationDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                self.created_interface = dialog.created_interface
                self.refresh_interface_list()
        else:
            # Each interface should provide its own dedicated creation dialog.
            # For now, we simply notify the user – specialised dialogs will be
            # implemented later once this manager tab is confirmed.
            QMessageBox.information(
                self,
                "Not implemented yet",
                f"Creation dialog for '{type_name}' is not implemented yet.\n"
                "After the interface manager GUI is confirmed, specialised "
                "dialogs will be added.",
            )

    # ------------------------------------------------------------------
    # Context menu handling
    # ------------------------------------------------------------------
    def _show_context_menu(self, position):
        menu = QMenu(self)
        edit_action = menu.addAction("Edit")
        info_action = menu.addAction("Info")
        delete_action = menu.addAction("Delete")

        action = menu.exec_(self.interface_table.viewport().mapToGlobal(position))
        if action == edit_action:
            self._handle_edit()
        elif action == info_action:
            self._handle_info()
        elif action == delete_action:
            self._handle_delete()

    def _selected_interface_name(self):
        row = self.interface_table.currentRow()
        if row < 0:
            return None
        return self.interface_table.item(row, 0).text()

    def _handle_edit(self):
        name = self._selected_interface_name()
        if not name:
            return
        iface = InterfaceBase.get(name)
        if iface is None:
            return

        # Resolve edit dialog based on class name to avoid issues with duplicate
        # module imports that can break `isinstance` checks.
        iface_type_name = iface.__class__.__name__

        if iface_type_name == "EmbeddedBeamSolidInterface":
            dialog = EmbeddedInterfaceEditDialog(iface, self)
            if dialog.exec_() == QDialog.Accepted:
                self.refresh_interface_list()
        else:
            QMessageBox.information(
                self,
                "Not implemented yet",
                f"Edit dialog for interface '{name}' of type '{iface_type_name}' is not yet implemented.",
            )

    def _handle_info(self):
        name = self._selected_interface_name()
        if not name:
            return
        iface = InterfaceBase.get(name)
        if iface is None:
            return
        details = [
            f"Name: {iface.name}",
            f"Type: {iface.__class__.__name__}",
            f"Owners: {', '.join(iface.owners)}",
        ]
        QMessageBox.information(self, f"Interface '{name}'", "\n".join(details))

    def _handle_delete(self):
        name = self._selected_interface_name()
        if not name:
            return
        reply = QMessageBox.question(
            self,
            "Delete Interface",
            f"Are you sure you want to delete interface '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                del InterfaceBase._registry[name]
            except KeyError:
                pass
            self.refresh_interface_list()

    def _clear_all_interfaces(self):
        reply = QMessageBox.question(
            self,
            "Clear All Interfaces",
            "Are you sure you want to delete all interfaces?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            InterfaceBase._registry.clear()
            self.refresh_interface_list() 

# Dialog classes now live in embedded_interface_gui.py 