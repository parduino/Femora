"""
GUI application for managing soil layers and visualizing transfer functions.

This module provides a graphical user interface for:
1. Managing soil layers (add, remove, modify)
2. Visualizing soil profiles
3. Computing and plotting transfer functions
4. Loading and analyzing time histories
"""
import sys
import os
import numpy as np
from typing import Dict, List, Optional
from qtpy.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                          QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                          QLineEdit, QGroupBox, QDialog, QFormLayout, 
                          QMessageBox, QSplitter, QTableWidgetItem, QHeaderView,
                          QFileDialog, QTextEdit, QRadioButton, QCheckBox)
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor, QBrush
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from femora.tools.transferFunction import TransferFunction, TimeHistory


class TransferFunctionGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transfer Function Calculator")
        self.setGeometry(100, 100, 1000, 800)

        # Initialize default soil profile and rock properties
        self.soil_profile = [
            {"h": 2.0, "vs": 200.0, "rho": 1500.0, "damping": 0.05},
            {"h": 54.0, "vs": 400.0, "rho": 1500.0, "damping": 0.05},
        ]
        self.rock = {
            "vs": 850.0,
            "rho": 1500.0,
            "damping": 0.05,
        }

        # Initialize transfer function
        self.tf = None
        
        # Initialize time histories list
        self.time_histories = []

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Create left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        splitter.addWidget(left_panel)

        # Create middle panel for soil profile
        middle_panel = QWidget()
        middle_panel.setFixedWidth(120)
        middle_layout = QVBoxLayout(middle_panel)
        splitter.addWidget(middle_panel)

        # Create right panel for transfer function
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        splitter.addWidget(right_panel)

        # Set up control panel
        self._create_control_panel(left_layout)
        
        # Set up soil profile panel
        self._create_soil_profile_panel(middle_layout)
        
        # Set up transfer function panel
        self._create_transfer_function_panel(right_layout)

    def _create_control_panel(self, layout):
        """Create the control panel with layer management and rock properties."""
        # Layer management section
        layer_group = QGroupBox("Layer Management")
        layer_layout = QVBoxLayout(layer_group)

        # Create table for layers
        self.layer_table = QTableWidget()
        self.layer_table.setColumnCount(4)
        self.layer_table.setHorizontalHeaderLabels(["h (m)", "vs (m/s)", "ρ (kg/m³)", "ξ"])
        self.layer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layer_table.verticalHeader().setVisible(False)
        self.layer_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        layer_layout.addWidget(self.layer_table)

        # Layer buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Layer")
        remove_btn = QPushButton("Remove Layer")
        move_up_btn = QPushButton("Move Up")
        move_down_btn = QPushButton("Move Down")
        
        add_btn.clicked.connect(self._add_layer)
        remove_btn.clicked.connect(self._remove_layer)
        move_up_btn.clicked.connect(self._move_layer_up)
        move_down_btn.clicked.connect(self._move_layer_down)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(move_up_btn)
        btn_layout.addWidget(move_down_btn)
        layer_layout.addLayout(btn_layout)
        layout.addWidget(layer_group)

        # Rock properties section
        rock_group = QGroupBox("Rock Properties")
        rock_layout = QFormLayout(rock_group)

        # Rock properties entries
        self.rock_entries = {}
        for prop in ["vs", "rho", "damping"]:
            self.rock_entries[prop] = QLineEdit()
            self.rock_entries[prop].setText(str(self.rock[prop]))
            rock_layout.addRow(f"{prop.upper()}:", self.rock_entries[prop])
        layout.addWidget(rock_group)

        # Analysis parameters
        param_group = QGroupBox("Analysis Parameters")
        param_layout = QFormLayout(param_group)

        self.f_max_entry = QLineEdit()
        self.f_max_entry.setText("20.0")
        param_layout.addRow("Max Frequency (Hz):", self.f_max_entry)
        layout.addWidget(param_group)

        # Time History section
        time_history_group = QGroupBox("Time Histories")
        time_history_layout = QVBoxLayout(time_history_group)

        # Create table for time histories
        self.time_history_table = QTableWidget()
        self.time_history_table.setColumnCount(5)
        self.time_history_table.setHorizontalHeaderLabels(["Selected", "Name", "Points", "dt (s)", "Duration (s)"])
        self.time_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.time_history_table.verticalHeader().setVisible(False)
        self.time_history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.time_history_table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Set the first column (checkbox) to be narrower
        self.time_history_table.setColumnWidth(0, 60)
        
        # Connect selection changed signal
        self.time_history_table.itemSelectionChanged.connect(self._on_time_history_selection_changed)
        # Connect item changed signal for checkbox exclusivity
        self.time_history_table.itemChanged.connect(self._on_time_history_item_changed)
        
        time_history_layout.addWidget(self.time_history_table)

        # Time history buttons
        time_history_btn_layout = QHBoxLayout()
        load_btn = QPushButton("Load Record")
        plot_input_btn = QPushButton("Plot Input")
        plot_surface_btn = QPushButton("Plot Surface")
        remove_th_btn = QPushButton("Remove Record")

        load_btn.clicked.connect(self._load_record_merged)
        plot_input_btn.clicked.connect(self._plot_input_motion)
        plot_surface_btn.clicked.connect(self._plot_surface_motion)
        remove_th_btn.clicked.connect(self._remove_time_history)

        time_history_btn_layout.addWidget(load_btn)
        time_history_btn_layout.addWidget(plot_input_btn)
        time_history_btn_layout.addWidget(plot_surface_btn)
        time_history_btn_layout.addWidget(remove_th_btn)
        time_history_layout.addLayout(time_history_btn_layout)
        
        layout.addWidget(time_history_group)

        # Add spacer to push update button to bottom
        layout.addStretch()

        # Add update button at the bottom
        update_btn = QPushButton("Update Analysis")
        update_btn.setMinimumHeight(40)  # Make button bigger
        update_btn.clicked.connect(self._update_all)
        layout.addWidget(update_btn)

        # Update layer table
        self._update_layer_table()

    def _create_soil_profile_panel(self, layout):
        """Create the soil profile plot panel."""
        self.fig_profile = Figure(figsize=(2, 8), dpi=100)
        self.ax_profile = self.fig_profile.add_subplot(111)
        self.canvas_profile = FigureCanvas(self.fig_profile)
        layout.addWidget(self.canvas_profile)

    def _create_transfer_function_panel(self, layout):
        """Create the transfer function plot panel with tabs."""
        from qtpy.QtWidgets import QTabWidget
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create main transfer function tab
        tf_tab = QWidget()
        tf_layout = QVBoxLayout(tf_tab)
        self.tab_widget.addTab(tf_tab, "Transfer Function")
        
        # Create the main transfer function plot in the first tab
        self.fig_tf = Figure(figsize=(6, 8))
        self.ax_tf = self.fig_tf.add_subplot(111)
        self.canvas_tf = FigureCanvas(self.fig_tf)
        tf_layout.addWidget(self.canvas_tf)
        
        # Dictionary to keep track of surface motion tabs
        self.surface_motion_tabs = {}

    def _update_time_history_table(self):
        """Update the time history table with current time histories."""
        self.time_history_table.setRowCount(len(self.time_histories))
        for i, th in enumerate(self.time_histories):
            # Create checkbox item
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.time_history_table.setItem(i, 0, checkbox_item)
            
            # Set name item (editable)
            name_item = QTableWidgetItem(th.metadata.get('filename', 'Unknown'))
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.time_history_table.setItem(i, 1, name_item)
            
            # Set other items (read-only)
            self.time_history_table.setItem(i, 2, QTableWidgetItem(str(th.npts)))
            self.time_history_table.setItem(i, 3, QTableWidgetItem(f"{th.dt:.3f}"))
            self.time_history_table.setItem(i, 4, QTableWidgetItem(f"{th.duration:.1f}"))
            
            # Make other columns read-only
            for col in [2, 3, 4]:
                self.time_history_table.item(i, col).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

    def _on_time_history_selection_changed(self):
        """Handle time history selection changes."""
        # Uncheck all checkboxes
        for row in range(self.time_history_table.rowCount()):
            self.time_history_table.item(row, 0).setCheckState(Qt.Unchecked)
        # Check the selected row
        current_row = self.time_history_table.currentRow()
        if current_row >= 0:
            self.time_history_table.item(current_row, 0).setCheckState(Qt.Checked)

    def _on_time_history_item_changed(self, item):
        """Ensure only one checkbox is checked at a time."""
        if item.column() == 0:
            if item.checkState() == Qt.Checked:
                # Uncheck all other checkboxes
                for row in range(self.time_history_table.rowCount()):
                    if row != item.row():
                        other = self.time_history_table.item(row, 0)
                        if other and other.checkState() == Qt.Checked:
                            other.setCheckState(Qt.Unchecked)

    def _get_selected_time_history(self) -> Optional[TimeHistory]:
        """Get the currently selected time history."""
        current_row = self.time_history_table.currentRow()
        if current_row >= 0 and current_row < len(self.time_histories):
            # Verify that the checkbox is checked
            if self.time_history_table.item(current_row, 0).checkState() == Qt.Checked:
                return self.time_histories[current_row]
        return None

    def _remove_time_history(self):
        """Remove the selected time history."""
        current_row = self.time_history_table.currentRow()
        if current_row >= 0:
            self.time_histories.pop(current_row)
            self._update_time_history_table()
            # Reset background of all rows
            for row in range(self.time_history_table.rowCount()):
                for col in range(self.time_history_table.columnCount()):
                    item = self.time_history_table.item(row, col)
                    if item:
                        item.setBackground(QBrush(QColor(255, 255, 255)))

    def _load_record_merged(self):
        """Show dialog to load a record, always requiring acceleration file, and optionally a time file."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Time History")
        layout = QVBoxLayout(dialog)

        # Acceleration file (always required)
        acc_file_hbox = QHBoxLayout()
        acc_file_label = QLabel("Acceleration File:")
        acc_file_edit = QLineEdit()
        acc_file_browse = QPushButton("Browse")
        acc_file_hbox.addWidget(acc_file_label)
        acc_file_hbox.addWidget(acc_file_edit)
        acc_file_hbox.addWidget(acc_file_browse)
        layout.addLayout(acc_file_hbox)

        # Checkbox for separate time file
        time_checkbox = QCheckBox("Provide time file separately")
        layout.addWidget(time_checkbox)

        # Time file (optional)
        time_file_hbox = QHBoxLayout()
        time_file_label = QLabel("Time File:")
        time_file_edit = QLineEdit()
        time_file_browse = QPushButton("Browse")
        time_file_hbox.addWidget(time_file_label)
        time_file_hbox.addWidget(time_file_edit)
        time_file_hbox.addWidget(time_file_browse)
        layout.addLayout(time_file_hbox)

        # Initially disable time file input
        time_file_edit.setEnabled(False)
        time_file_browse.setEnabled(False)
        def update_time_file():
            enabled = time_checkbox.isChecked()
            time_file_edit.setEnabled(enabled)
            time_file_browse.setEnabled(enabled)
        time_checkbox.stateChanged.connect(update_time_file)
        update_time_file()

        # Browse logic
        def browse_acc():
            file_path, _ = QFileDialog.getOpenFileName(dialog, "Select Acceleration File", "", "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)")
            if file_path:
                acc_file_edit.setText(file_path)
        def browse_time():
            file_path, _ = QFileDialog.getOpenFileName(dialog, "Select Time File", "", "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)")
            if file_path:
                time_file_edit.setText(file_path)
        acc_file_browse.clicked.connect(browse_acc)
        time_file_browse.clicked.connect(browse_time)

        # Dialog buttons
        btns = QHBoxLayout()
        ok_btn = QPushButton("Load")
        cancel_btn = QPushButton("Cancel")
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted:
            acc_path = acc_file_edit.text().strip()
            if not acc_path:
                QMessageBox.warning(self, "Warning", "Acceleration file must be selected.")
                return
            if time_checkbox.isChecked():
                time_path = time_file_edit.text().strip()
                if not time_path:
                    QMessageBox.warning(self, "Warning", "Time file must be selected if checkbox is checked.")
                    return
                try:
                    time_history = TimeHistory.load(
                        time_file=time_path,
                        acc_file=acc_path,
                        delimiter=',',
                        skiprows=0
                    )
                    if not time_history.metadata:
                        time_history.metadata = {}
                    time_history.metadata.update({
                        'filename': f"{os.path.basename(time_path)} & {os.path.basename(acc_path)}",
                        'format': 'separate_files',
                    })
                    self.time_histories.append(time_history)
                    self._update_time_history_table()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load time histories: {str(e)}")
            else:
                try:
                    time_history = TimeHistory.load(file_path=acc_path)
                    self.time_histories.append(time_history)
                    self._update_time_history_table()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load time history: {str(e)}")

    def _plot_input_motion(self):
        """Plot the input motion."""
        time_history = self._get_selected_time_history()
        if time_history is None:
            QMessageBox.warning(self, "Warning", "No time history selected")
            return

        plt.figure(figsize=(10, 6))
        plt.plot(time_history.time, time_history.acceleration)
        plt.xlabel("Time (s)")
        plt.ylabel("Acceleration (g)")
        plt.title(f"Input Motion - {time_history.metadata.get('filename', 'Unknown')}")
        plt.grid(True)
        plt.show()

    def _plot_surface_motion(self):
        """Plot the surface motion in a new tab using the TransferFunction's plot_surface_motion method."""
        if self.tf is None:
            QMessageBox.warning(self, "Warning", "Please run 'Update Analysis' first")
            return
            
        time_history = self._get_selected_time_history()
        if time_history is None:
            QMessageBox.warning(self, "Warning", "No time history selected")
            return

        try:
            # Get the record name to use as tab title
            record_name = time_history.metadata.get('filename', 'Unknown')
            
            # Check if we already have a tab for this record
            if record_name in self.surface_motion_tabs:
                # If yes, switch to that tab
                tab_index = self.tab_widget.indexOf(self.surface_motion_tabs[record_name]['tab'])
                self.tab_widget.setCurrentIndex(tab_index)
                return
                
            # Create a new tab for this record
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            
            # Create figure for the surface motion plot
            fig = Figure(figsize=(6, 8))
            canvas = FigureCanvas(fig)
            tab_layout.addWidget(canvas)
            
            # Use the TransferFunction's plot_surface_motion method with our figure
            self.tf.plot_surface_motion(time_history, fig=fig)
            
            # Add the tab to the tab widget
            tab_index = self.tab_widget.addTab(tab, record_name)
            
            # Store reference to the tab and its components
            self.surface_motion_tabs[record_name] = {
                'tab': tab,
                'figure': fig,
                'canvas': canvas
            }
            
            # Switch to the new tab
            self.tab_widget.setCurrentIndex(tab_index)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to compute surface motion: {str(e)}")

    def _update_layer_table(self):
        """Update the layer table with current soil profile."""
        self.layer_table.setRowCount(len(self.soil_profile))
        for i, layer in enumerate(self.soil_profile):
            self.layer_table.setItem(i, 0, QTableWidgetItem(f"{layer['h']:.2f}"))
            self.layer_table.setItem(i, 1, QTableWidgetItem(f"{layer['vs']:.0f}"))
            self.layer_table.setItem(i, 2, QTableWidgetItem(f"{layer['rho']:.0f}"))
            self.layer_table.setItem(i, 3, QTableWidgetItem(f"{layer['damping']:.3f}"))

    def _update_all(self):
        """Update all parameters and run analysis."""
        try:
            # Check if there are any layers
            if self.layer_table.rowCount() == 0:
                raise ValueError("At least one layer is required")

            # Update soil profile
            new_profile = []
            for row in range(self.layer_table.rowCount()):
                layer = {
                    'h': float(self.layer_table.item(row, 0).text()),
                    'vs': float(self.layer_table.item(row, 1).text()),
                    'rho': float(self.layer_table.item(row, 2).text()),
                    'damping': float(self.layer_table.item(row, 3).text())
                }
                if any(v <= 0 for v in layer.values()):
                    raise ValueError("All layer values must be positive")
                new_profile.append(layer)
            self.soil_profile = new_profile

            # Update rock properties
            self.rock = {
                "vs": float(self.rock_entries["vs"].text()),
                "rho": float(self.rock_entries["rho"].text()),
                "damping": float(self.rock_entries["damping"].text())
            }
            if any(v <= 0 for v in self.rock.values()):
                raise ValueError("All rock values must be positive")



            # Create new transfer function
            f_max = float(self.f_max_entry.text())
            if f_max <= 0:
                raise ValueError("Maximum frequency must be positive")
            
            if self.tf is None:
                self.tf = TransferFunction(
                    soil_profile=self.soil_profile,
                    rock=self.rock,
                    f_max=f_max
                )
            else:
                self.tf.update_soil_profile(self.soil_profile)
                self.tf.update_rock(self.rock)
                self.tf.update_frequency(f_max)

            
            # Update plots
            self._calculate_transfer_function()
            
            # Update time history info if available
            self._update_time_history_table()
                
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))
            self._update_layer_table()

    def _add_layer(self):
        """Add a new layer."""
        # First update the soil profile with any modifications in the table
        try:
            new_profile = []
            for row in range(self.layer_table.rowCount()):
                layer = {
                    'h': float(self.layer_table.item(row, 0).text()),
                    'vs': float(self.layer_table.item(row, 1).text()),
                    'rho': float(self.layer_table.item(row, 2).text()),
                    'damping': float(self.layer_table.item(row, 3).text())
                }
                new_profile.append(layer)
            self.soil_profile = new_profile
        except (ValueError, AttributeError):
            # If there's an error reading the table, revert to previous state
            self._update_layer_table()
            return

        # Add default layer
        new_layer = {"h": 10.0, "vs": 300.0, "rho": 1500.0, "damping": 0.05}
        self.soil_profile.append(new_layer)
        self._update_layer_table()

    def _remove_layer(self):
        """Remove selected layer."""
        current = self.layer_table.currentRow()
        if current >= 0:
            if len(self.soil_profile) <= 1:
                QMessageBox.warning(self, "Cannot Remove Layer", 
                                  "At least one layer must remain in the soil profile.")
                return
            self.soil_profile.pop(current)
            self._update_layer_table()

    def _move_layer_up(self):
        """Move selected layer up."""
        current = self.layer_table.currentRow()
        if current > 0:
            self.soil_profile[current], self.soil_profile[current-1] = \
                self.soil_profile[current-1], self.soil_profile[current]
            self._update_layer_table()
            self.layer_table.selectRow(current-1)

    def _move_layer_down(self):
        """Move selected layer down."""
        current = self.layer_table.currentRow()
        if current >= 0 and current < len(self.soil_profile) - 1:
            self.soil_profile[current], self.soil_profile[current+1] = \
                self.soil_profile[current+1], self.soil_profile[current]
            self._update_layer_table()
            self.layer_table.selectRow(current+1)

    def _calculate_transfer_function(self):
        """Update transfer function and plots."""
        if self.tf is None:
            # Remove all axes from the figures and show a blank white area
            self.fig_profile.clf()
            self.fig_tf.clf()
            self.fig_profile.patch.set_facecolor('white')
            self.fig_tf.patch.set_facecolor('white')
            self.canvas_profile.draw()
            self.canvas_tf.draw()
            # Do NOT use self.ax_profile or self.ax_tf here!
            return
        try:
            # Recreate axes after blanking
            self.fig_profile.clf()
            self.fig_tf.clf()
            self.ax_profile = self.fig_profile.add_subplot(111)
            self.ax_tf = self.fig_tf.add_subplot(111)
            # Update soil profile plot
            self.ax_profile.clear()
            self._plot_soil_profile(self.tf)
            # Update transfer function plot
            if not self.tf.computed:
                self.tf.compute()
            self.ax_tf.clear()
            self._plot_transfer_function(self.tf)
            self.fig_profile.tight_layout()
            self.fig_tf.tight_layout()
            self.canvas_profile.draw()
            self.canvas_tf.draw()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _plot_soil_profile(self, tf: TransferFunction):
        """Plot the soil profile using the TransferFunction's plot_soil_profile method."""
        tf.plot_soil_profile(self.ax_profile)

    def _plot_transfer_function(self, tf: TransferFunction):
        """Plot the transfer function using the TransferFunction's plot method."""
        tf.plot(plot_type='uu', ax=self.ax_tf)


def main():
    """Run the GUI application."""
    app = QApplication(sys.argv)
    window = TransferFunctionGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()