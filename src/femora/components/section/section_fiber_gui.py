"""
Improved Fiber Section GUI that collects all data before creating the section
No temporary instances - everything is stored in data structures until confirmation
"""

from qtpy.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
    QDialog, QFormLayout, QMessageBox, QHeaderView, QGridLayout,
    QTabWidget, QGroupBox, QSpinBox, QDoubleSpinBox, QTextEdit,
    QFrame, QSplitter, QListWidget, QListWidgetItem, QCheckBox
)

from femora.components.section.section_opensees import (
    FiberSection, FiberElement, RectangularPatch, QuadrilateralPatch, 
    CircularPatch, StraightLayer
)
from femora.components.Material.materialBase import Material


class FiberSectionDialog(QDialog):
    """
    Improved dialog for creating and editing fiber sections
    Collects all data before creating the actual section
    """
    
    def __init__(self, fiber_section=None, parent=None):
        super().__init__(parent)
        self.fiber_section = fiber_section
        self.is_editing = fiber_section is not None
        
        self.setWindowTitle("Edit Fiber Section" if self.is_editing else "Create Fiber Section")
        self.setGeometry(200, 200, 1200, 800)
        
        # Data storage for components (instead of temporary section)
        self.fibers_data = []
        self.patches_data = []
        self.layers_data = []
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Basic section information
        self.setup_basic_info(main_layout)
        
        # Main content area with tabs
        self.setup_content_tabs(main_layout)
        
        # Buttons
        self.setup_buttons(main_layout)
        
        # Initialize data if editing
        if self.is_editing:
            self.load_existing_data()
        
        # Refresh materials
        self.refresh_materials()

    def setup_basic_info(self, main_layout):
        """Setup basic section information inputs"""
        info_group = QGroupBox("Section Information")
        info_layout = QGridLayout(info_group)
        
        # Section name
        self.name_input = QLineEdit()
        if self.is_editing:
            self.name_input.setText(self.fiber_section.user_name)
        info_layout.addWidget(QLabel("Section Name:"), 0, 0)
        info_layout.addWidget(self.name_input, 0, 1)
        
        # Optional GJ parameter
        self.gj_checkbox = QCheckBox("Include Torsional Stiffness (GJ)")
        self.gj_input = QDoubleSpinBox()
        self.gj_input.setRange(0.001, 1e12)
        self.gj_input.setDecimals(3)
        self.gj_input.setEnabled(False)
        
        self.gj_checkbox.toggled.connect(self.gj_input.setEnabled)
        
        if self.is_editing and self.fiber_section.GJ is not None:
            self.gj_checkbox.setChecked(True)
            self.gj_input.setValue(self.fiber_section.GJ)
        
        info_layout.addWidget(self.gj_checkbox, 1, 0)
        info_layout.addWidget(self.gj_input, 1, 1)
        
        main_layout.addWidget(info_group)

    def setup_content_tabs(self, main_layout):
        """Setup main content area with tabs"""
        self.tab_widget = QTabWidget()
        
        # Individual Fibers tab
        self.setup_fibers_tab()
        
        # Patches tab
        self.setup_patches_tab()
        
        # Layers tab  
        self.setup_layers_tab()
        
        # Preview tab with plot
        self.setup_preview_tab()
        
        main_layout.addWidget(self.tab_widget)

    def setup_fibers_tab(self):
        """Setup tab for individual fiber management"""
        fibers_widget = QWidget()
        layout = QHBoxLayout(fibers_widget)
        
        # Left side - fiber list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        left_layout.addWidget(QLabel("Individual Fibers:"))
        
        self.fibers_table = QTableWidget()
        self.fibers_table.setColumnCount(5)  # Y, Z, Area, Material, Delete
        self.fibers_table.setHorizontalHeaderLabels(["Y", "Z", "Area", "Material", "Delete"])
        header = self.fibers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        left_layout.addWidget(self.fibers_table)
        
        layout.addWidget(left_panel)
        
        # Right side - fiber creation form
        right_panel = QGroupBox("Add Fiber")
        right_layout = QFormLayout(right_panel)
        
        self.fiber_y_input = QDoubleSpinBox()
        self.fiber_y_input.setRange(-1e6, 1e6)
        self.fiber_y_input.setDecimals(6)
        right_layout.addRow("Y Coordinate:", self.fiber_y_input)
        
        self.fiber_z_input = QDoubleSpinBox()
        self.fiber_z_input.setRange(-1e6, 1e6)
        self.fiber_z_input.setDecimals(6)
        right_layout.addRow("Z Coordinate:", self.fiber_z_input)
        
        self.fiber_area_input = QDoubleSpinBox()
        self.fiber_area_input.setRange(0.001, 1e6)
        self.fiber_area_input.setDecimals(6)
        right_layout.addRow("Area:", self.fiber_area_input)
        
        self.fiber_material_combo = QComboBox()
        right_layout.addRow("Material:", self.fiber_material_combo)
        
        add_fiber_btn = QPushButton("Add Fiber")
        add_fiber_btn.clicked.connect(self.add_fiber_data)
        right_layout.addRow(add_fiber_btn)
        
        layout.addWidget(right_panel)
        
        self.tab_widget.addTab(fibers_widget, "Individual Fibers")

    def setup_patches_tab(self):
        """Setup tab for patch management"""
        patches_widget = QWidget()
        layout = QVBoxLayout(patches_widget)
        
        # Patch type selection
        patch_type_layout = QHBoxLayout()
        patch_type_layout.addWidget(QLabel("Patch Type:"))
        
        self.patch_type_combo = QComboBox()
        self.patch_type_combo.addItems(["Rectangular", "Quadrilateral", "Circular"])
        self.patch_type_combo.currentTextChanged.connect(self.patch_type_changed)
        patch_type_layout.addWidget(self.patch_type_combo)
        
        patch_type_layout.addStretch()
        layout.addLayout(patch_type_layout)
        
        # Patch content area
        patch_content = QHBoxLayout()
        
        # Left side - patches table
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        left_layout.addWidget(QLabel("Patches:"))
        
        self.patches_table = QTableWidget()
        self.patches_table.setColumnCount(4)  # Type, Material, Fibers, Delete
        self.patches_table.setHorizontalHeaderLabels(["Type", "Material", "Est. Fibers", "Delete"])
        header = self.patches_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        left_layout.addWidget(self.patches_table)
        
        patch_content.addWidget(left_panel)
        
        # Right side - patch creation forms
        self.setup_patch_forms(patch_content)
        
        layout.addLayout(patch_content)
        self.tab_widget.addTab(patches_widget, "Patches")

    def setup_patch_forms(self, patch_content):
        """Setup patch creation forms"""
        self.patch_forms_widget = QWidget()
        self.patch_forms_layout = QVBoxLayout(self.patch_forms_widget)
        
        # Rectangular patch form
        self.rect_patch_form = QGroupBox("Rectangular Patch")
        layout = QFormLayout(self.rect_patch_form)
        
        self.rect_material_combo = QComboBox()
        layout.addRow("Material:", self.rect_material_combo)
        
        self.rect_subdiv_y = QSpinBox()
        self.rect_subdiv_y.setRange(1, 1000)
        self.rect_subdiv_y.setValue(10)
        layout.addRow("Y Subdivisions:", self.rect_subdiv_y)
        
        self.rect_subdiv_z = QSpinBox()
        self.rect_subdiv_z.setRange(1, 1000)
        self.rect_subdiv_z.setValue(10)
        layout.addRow("Z Subdivisions:", self.rect_subdiv_z)
        
        self.rect_y1 = QDoubleSpinBox()
        self.rect_y1.setRange(-1e6, 1e6)
        self.rect_y1.setDecimals(6)
        layout.addRow("Y1 (min):", self.rect_y1)
        
        self.rect_z1 = QDoubleSpinBox()
        self.rect_z1.setRange(-1e6, 1e6)
        self.rect_z1.setDecimals(6)
        layout.addRow("Z1 (min):", self.rect_z1)
        
        self.rect_y2 = QDoubleSpinBox()
        self.rect_y2.setRange(-1e6, 1e6)
        self.rect_y2.setDecimals(6)
        layout.addRow("Y2 (max):", self.rect_y2)
        
        self.rect_z2 = QDoubleSpinBox()
        self.rect_z2.setRange(-1e6, 1e6)
        self.rect_z2.setDecimals(6)
        layout.addRow("Z2 (max):", self.rect_z2)
        
        add_rect_btn = QPushButton("Add Rectangular Patch")
        add_rect_btn.clicked.connect(self.add_rectangular_patch_data)
        layout.addRow(add_rect_btn)
        
        self.patch_forms_layout.addWidget(self.rect_patch_form)
        
        # Quadrilateral patch form
        self.quad_patch_form = QGroupBox("Quadrilateral Patch")
        quad_layout = QFormLayout(self.quad_patch_form)
        
        self.quad_material_combo = QComboBox()
        quad_layout.addRow("Material:", self.quad_material_combo)
        
        self.quad_subdiv_ij = QSpinBox()
        self.quad_subdiv_ij.setRange(1, 1000)
        self.quad_subdiv_ij.setValue(10)
        quad_layout.addRow("I-J Subdivisions:", self.quad_subdiv_ij)
        
        self.quad_subdiv_jk = QSpinBox()
        self.quad_subdiv_jk.setRange(1, 1000)
        self.quad_subdiv_jk.setValue(10)
        quad_layout.addRow("J-K Subdivisions:", self.quad_subdiv_jk)
        
        # Vertices (I, J, K, L) in a grid layout
        vertices_group = QGroupBox("Vertices (Counter-clockwise: I → J → K → L)")
        vertices_layout = QGridLayout(vertices_group)
        
        self.quad_vertices = {}
        for i, vertex in enumerate(['I', 'J', 'K', 'L']):
            vertices_layout.addWidget(QLabel(f"Vertex {vertex}:"), i, 0)
            
            y_spin = QDoubleSpinBox()
            y_spin.setRange(-1e6, 1e6)
            y_spin.setDecimals(6)
            vertices_layout.addWidget(QLabel("Y:"), i, 1)
            vertices_layout.addWidget(y_spin, i, 2)
            
            z_spin = QDoubleSpinBox()
            z_spin.setRange(-1e6, 1e6)
            z_spin.setDecimals(6)
            vertices_layout.addWidget(QLabel("Z:"), i, 3)
            vertices_layout.addWidget(z_spin, i, 4)
            
            self.quad_vertices[vertex] = {'y': y_spin, 'z': z_spin}
        
        quad_layout.addRow(vertices_group)
        
        add_quad_btn = QPushButton("Add Quadrilateral Patch")
        add_quad_btn.clicked.connect(self.add_quadrilateral_patch_data)
        quad_layout.addRow(add_quad_btn)
        
        self.quad_patch_form.setVisible(False)
        self.patch_forms_layout.addWidget(self.quad_patch_form)
        
        # Circular patch form
        self.circ_patch_form = QGroupBox("Circular Patch")
        circ_layout = QFormLayout(self.circ_patch_form)
        
        self.circ_material_combo = QComboBox()
        circ_layout.addRow("Material:", self.circ_material_combo)
        
        self.circ_subdiv_circ = QSpinBox()
        self.circ_subdiv_circ.setRange(1, 1000)
        self.circ_subdiv_circ.setValue(16)
        circ_layout.addRow("Circumferential Subdivisions:", self.circ_subdiv_circ)
        
        self.circ_subdiv_rad = QSpinBox()
        self.circ_subdiv_rad.setRange(1, 1000)
        self.circ_subdiv_rad.setValue(4)
        circ_layout.addRow("Radial Subdivisions:", self.circ_subdiv_rad)
        
        self.circ_y_center = QDoubleSpinBox()
        self.circ_y_center.setRange(-1e6, 1e6)
        self.circ_y_center.setDecimals(6)
        circ_layout.addRow("Y Center:", self.circ_y_center)
        
        self.circ_z_center = QDoubleSpinBox()
        self.circ_z_center.setRange(-1e6, 1e6)
        self.circ_z_center.setDecimals(6)
        circ_layout.addRow("Z Center:", self.circ_z_center)
        
        self.circ_int_rad = QDoubleSpinBox()
        self.circ_int_rad.setRange(0.0, 1e6)
        self.circ_int_rad.setDecimals(6)
        circ_layout.addRow("Inner Radius:", self.circ_int_rad)
        
        self.circ_ext_rad = QDoubleSpinBox()
        self.circ_ext_rad.setRange(0.001, 1e6)
        self.circ_ext_rad.setDecimals(6)
        circ_layout.addRow("Outer Radius:", self.circ_ext_rad)
        
        # Optional angle parameters
        self.circ_use_angles = QCheckBox("Specify Custom Angles")
        circ_layout.addRow(self.circ_use_angles)
        
        self.circ_start_ang = QDoubleSpinBox()
        self.circ_start_ang.setRange(0, 360)
        self.circ_start_ang.setDecimals(1)
        self.circ_start_ang.setValue(0)
        self.circ_start_ang.setEnabled(False)
        circ_layout.addRow("Start Angle (deg):", self.circ_start_ang)
        
        self.circ_end_ang = QDoubleSpinBox()
        self.circ_end_ang.setRange(0, 360)
        self.circ_end_ang.setDecimals(1)
        self.circ_end_ang.setValue(360)
        self.circ_end_ang.setEnabled(False)
        circ_layout.addRow("End Angle (deg):", self.circ_end_ang)
        
        self.circ_use_angles.toggled.connect(self.circ_start_ang.setEnabled)
        self.circ_use_angles.toggled.connect(self.circ_end_ang.setEnabled)
        
        add_circ_btn = QPushButton("Add Circular Patch")
        add_circ_btn.clicked.connect(self.add_circular_patch_data)
        circ_layout.addRow(add_circ_btn)
        
        self.circ_patch_form.setVisible(False)
        self.patch_forms_layout.addWidget(self.circ_patch_form)
        
        patch_content.addWidget(self.patch_forms_widget)

    def setup_layers_tab(self):
        """Setup tab for layer management"""
        layers_widget = QWidget()
        layout = QHBoxLayout(layers_widget)
        
        # Left side - layers table
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        left_layout.addWidget(QLabel("Layers:"))
        
        self.layers_table = QTableWidget()
        self.layers_table.setColumnCount(4)  # Type, Material, Fibers, Delete
        self.layers_table.setHorizontalHeaderLabels(["Type", "Material", "Fibers", "Delete"])
        header = self.layers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        left_layout.addWidget(self.layers_table)
        
        layout.addWidget(left_panel)
        
        # Right side - layer creation form
        right_panel = QGroupBox("Add Straight Layer")
        right_layout = QFormLayout(right_panel)
        
        self.layer_material_combo = QComboBox()
        right_layout.addRow("Material:", self.layer_material_combo)
        
        self.layer_num_fibers = QSpinBox()
        self.layer_num_fibers.setRange(1, 1000)
        self.layer_num_fibers.setValue(5)
        right_layout.addRow("Number of Fibers:", self.layer_num_fibers)
        
        self.layer_area_per_fiber = QDoubleSpinBox()
        self.layer_area_per_fiber.setRange(0.001, 1e6)
        self.layer_area_per_fiber.setDecimals(6)
        right_layout.addRow("Area per Fiber:", self.layer_area_per_fiber)
        
        self.layer_y1 = QDoubleSpinBox()
        self.layer_y1.setRange(-1e6, 1e6)
        self.layer_y1.setDecimals(6)
        right_layout.addRow("Start Y:", self.layer_y1)
        
        self.layer_z1 = QDoubleSpinBox()
        self.layer_z1.setRange(-1e6, 1e6)
        self.layer_z1.setDecimals(6)
        right_layout.addRow("Start Z:", self.layer_z1)
        
        self.layer_y2 = QDoubleSpinBox()
        self.layer_y2.setRange(-1e6, 1e6)
        self.layer_y2.setDecimals(6)
        right_layout.addRow("End Y:", self.layer_y2)
        
        self.layer_z2 = QDoubleSpinBox()
        self.layer_z2.setRange(-1e6, 1e6)
        self.layer_z2.setDecimals(6)
        right_layout.addRow("End Z:", self.layer_z2)
        
        add_layer_btn = QPushButton("Add Layer")
        add_layer_btn.clicked.connect(self.add_layer_data)
        right_layout.addRow(add_layer_btn)
        
        layout.addWidget(right_panel)
        
        self.tab_widget.addTab(layers_widget, "Layers")

    def setup_preview_tab(self):
        """Setup preview tab with plot"""
        preview_widget = QWidget()
        layout = QVBoxLayout(preview_widget)
        
        # Plot controls
        controls_layout = QHBoxLayout()
        
        self.plot_section_btn = QPushButton("Update Plot")
        self.plot_section_btn.clicked.connect(self.update_plot)
        controls_layout.addWidget(self.plot_section_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Plot area
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Section info
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(150)
        self.info_text.setReadOnly(True)
        layout.addWidget(self.info_text)
        
        self.tab_widget.addTab(preview_widget, "Preview")

    def setup_buttons(self, main_layout):
        """Setup dialog buttons"""
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept_changes)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)

    def refresh_materials(self):
        """Refresh all material combo boxes"""
        materials = list(Material.get_all_materials().values())
        
        for combo in [self.fiber_material_combo, self.rect_material_combo, 
                     self.quad_material_combo, self.circ_material_combo, self.layer_material_combo]:
            combo.clear()
            combo.addItem("Select Material", None)
            for material in materials:
                combo.addItem(f"{material.user_name} (Tag: {material.tag})", material)

    def patch_type_changed(self, patch_type):
        """Handle patch type selection change"""
        # Hide all patch forms
        self.rect_patch_form.setVisible(False)
        self.quad_patch_form.setVisible(False)
        self.circ_patch_form.setVisible(False)
        
        # Show selected patch form
        if patch_type == "Rectangular":
            self.rect_patch_form.setVisible(True)
        elif patch_type == "Quadrilateral":
            self.quad_patch_form.setVisible(True)
        elif patch_type == "Circular":
            self.circ_patch_form.setVisible(True)

    def add_fiber_data(self):
        """Add fiber data to storage"""
        try:
            y_loc = self.fiber_y_input.value()
            z_loc = self.fiber_z_input.value()
            area = self.fiber_area_input.value()
            material = self.fiber_material_combo.currentData()
            
            if material is None:
                QMessageBox.warning(self, "Error", "Please select a material")
                return
            
            # Store fiber data
            fiber_data = {
                'y_loc': y_loc,
                'z_loc': z_loc,
                'area': area,
                'material': material
            }
            self.fibers_data.append(fiber_data)
            self.update_fibers_table()
            
            # Clear inputs
            self.fiber_y_input.setValue(0)
            self.fiber_z_input.setValue(0)
            self.fiber_area_input.setValue(0)
            self.fiber_material_combo.setCurrentIndex(0)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add fiber: {str(e)}")

    def add_rectangular_patch_data(self):
        """Add rectangular patch data to storage"""
        try:
            material = self.rect_material_combo.currentData()
            if material is None:
                QMessageBox.warning(self, "Error", "Please select a material")
                return
            
            # Store patch data
            patch_data = {
                'type': 'Rectangular',
                'material': material,
                'num_subdiv_y': self.rect_subdiv_y.value(),
                'num_subdiv_z': self.rect_subdiv_z.value(),
                'y1': self.rect_y1.value(),
                'z1': self.rect_z1.value(),
                'y2': self.rect_y2.value(),
                'z2': self.rect_z2.value()
            }
            self.patches_data.append(patch_data)
            self.update_patches_table()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add patch: {str(e)}")

    def add_quadrilateral_patch_data(self):
        """Add quadrilateral patch data to storage"""
        try:
            material = self.quad_material_combo.currentData()
            if material is None:
                QMessageBox.warning(self, "Error", "Please select a material")
                return
            
            # Collect vertices
            vertices = []
            for vertex in ['I', 'J', 'K', 'L']:
                y = self.quad_vertices[vertex]['y'].value()
                z = self.quad_vertices[vertex]['z'].value()
                vertices.append((y, z))
            
            # Store patch data
            patch_data = {
                'type': 'Quadrilateral',
                'material': material,
                'num_subdiv_ij': self.quad_subdiv_ij.value(),
                'num_subdiv_jk': self.quad_subdiv_jk.value(),
                'vertices': vertices
            }
            self.patches_data.append(patch_data)
            self.update_patches_table()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add quadrilateral patch: {str(e)}")

    def add_circular_patch_data(self):
        """Add circular patch data to storage"""
        try:
            material = self.circ_material_combo.currentData()
            if material is None:
                QMessageBox.warning(self, "Error", "Please select a material")
                return
            
            # Get angle parameters
            start_ang = self.circ_start_ang.value() if self.circ_use_angles.isChecked() else None
            end_ang = self.circ_end_ang.value() if self.circ_use_angles.isChecked() else None
            
            # Store patch data
            patch_data = {
                'type': 'Circular',
                'material': material,
                'num_subdiv_circ': self.circ_subdiv_circ.value(),
                'num_subdiv_rad': self.circ_subdiv_rad.value(),
                'y_center': self.circ_y_center.value(),
                'z_center': self.circ_z_center.value(),
                'int_rad': self.circ_int_rad.value(),
                'ext_rad': self.circ_ext_rad.value(),
                'start_ang': start_ang,
                'end_ang': end_ang
            }
            self.patches_data.append(patch_data)
            self.update_patches_table()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add circular patch: {str(e)}")

    def add_layer_data(self):
        """Add layer data to storage"""
        try:
            material = self.layer_material_combo.currentData()
            if material is None:
                QMessageBox.warning(self, "Error", "Please select a material")
                return
            
            # Store layer data
            layer_data = {
                'type': 'Straight',
                'material': material,
                'num_fibers': self.layer_num_fibers.value(),
                'area_per_fiber': self.layer_area_per_fiber.value(),
                'y1': self.layer_y1.value(),
                'z1': self.layer_z1.value(),
                'y2': self.layer_y2.value(),
                'z2': self.layer_z2.value()
            }
            self.layers_data.append(layer_data)
            self.update_layers_table()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add layer: {str(e)}")
        """Add layer data to storage"""
        try:
            material = self.layer_material_combo.currentData()
            if material is None:
                QMessageBox.warning(self, "Error", "Please select a material")
                return
            
            # Store layer data
            layer_data = {
                'type': 'Straight',
                'material': material,
                'num_fibers': self.layer_num_fibers.value(),
                'area_per_fiber': self.layer_area_per_fiber.value(),
                'y1': self.layer_y1.value(),
                'z1': self.layer_z1.value(),
                'y2': self.layer_y2.value(),
                'z2': self.layer_z2.value()
            }
            self.layers_data.append(layer_data)
            self.update_layers_table()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add layer: {str(e)}")

    def update_fibers_table(self):
        """Update the fibers table"""
        self.fibers_table.setRowCount(len(self.fibers_data))
        
        for row, fiber_data in enumerate(self.fibers_data):
            self.fibers_table.setItem(row, 0, QTableWidgetItem(str(fiber_data['y_loc'])))
            self.fibers_table.setItem(row, 1, QTableWidgetItem(str(fiber_data['z_loc'])))
            self.fibers_table.setItem(row, 2, QTableWidgetItem(str(fiber_data['area'])))
            self.fibers_table.setItem(row, 3, QTableWidgetItem(fiber_data['material'].user_name))
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_fiber_data(r))
            self.fibers_table.setCellWidget(row, 4, delete_btn)

    def update_patches_table(self):
        """Update the patches table"""
        self.patches_table.setRowCount(len(self.patches_data))
        
        for row, patch_data in enumerate(self.patches_data):
            self.patches_table.setItem(row, 0, QTableWidgetItem(patch_data['type']))
            self.patches_table.setItem(row, 1, QTableWidgetItem(patch_data['material'].user_name))
            
            # Calculate estimated fibers
            if patch_data['type'] == 'Rectangular':
                est_fibers = patch_data['num_subdiv_y'] * patch_data['num_subdiv_z']
            elif patch_data['type'] == 'Quadrilateral':
                est_fibers = patch_data['num_subdiv_ij'] * patch_data['num_subdiv_jk']
            elif patch_data['type'] == 'Circular':
                est_fibers = patch_data['num_subdiv_circ'] * patch_data['num_subdiv_rad']
            else:
                est_fibers = "Unknown"
            
            self.patches_table.setItem(row, 2, QTableWidgetItem(str(est_fibers)))
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_patch_data(r))
            self.patches_table.setCellWidget(row, 3, delete_btn)

    def update_layers_table(self):
        """Update the layers table"""
        self.layers_table.setRowCount(len(self.layers_data))
        
        for row, layer_data in enumerate(self.layers_data):
            self.layers_table.setItem(row, 0, QTableWidgetItem(layer_data['type']))
            self.layers_table.setItem(row, 1, QTableWidgetItem(layer_data['material'].user_name))
            self.layers_table.setItem(row, 2, QTableWidgetItem(str(layer_data['num_fibers'])))
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_layer_data(r))
            self.layers_table.setCellWidget(row, 3, delete_btn)

    def delete_fiber_data(self, row):
        """Delete fiber data"""
        if 0 <= row < len(self.fibers_data):
            del self.fibers_data[row]
            self.update_fibers_table()

    def delete_patch_data(self, row):
        """Delete patch data"""
        if 0 <= row < len(self.patches_data):
            del self.patches_data[row]
            self.update_patches_table()

    def delete_layer_data(self, row):
        """Delete layer data"""
        if 0 <= row < len(self.layers_data):
            del self.layers_data[row]
            self.update_layers_table()

    def update_plot(self):
        """Update the plot using static plotting method"""
        try:
            # Create temporary objects for plotting
            fibers = []
            patches = []
            layers = []
            
            # Create fiber objects
            for fiber_data in self.fibers_data:
                fiber = FiberElement(
                    fiber_data['y_loc'],
                    fiber_data['z_loc'],
                    fiber_data['area'],
                    fiber_data['material']
                )
                fibers.append(fiber)
            
            # Create patch objects
            for patch_data in self.patches_data:
                if patch_data['type'] == 'Rectangular':
                    patch = RectangularPatch(
                        patch_data['material'],
                        patch_data['num_subdiv_y'],
                        patch_data['num_subdiv_z'],
                        patch_data['y1'],
                        patch_data['z1'],
                        patch_data['y2'],
                        patch_data['z2']
                    )
                    patches.append(patch)
                elif patch_data['type'] == 'Quadrilateral':
                    patch = QuadrilateralPatch(
                        patch_data['material'],
                        patch_data['num_subdiv_ij'],
                        patch_data['num_subdiv_jk'],
                        patch_data['vertices']
                    )
                    patches.append(patch)
                elif patch_data['type'] == 'Circular':
                    patch = CircularPatch(
                        patch_data['material'],
                        patch_data['num_subdiv_circ'],
                        patch_data['num_subdiv_rad'],
                        patch_data['y_center'],
                        patch_data['z_center'],
                        patch_data['int_rad'],
                        patch_data['ext_rad'],
                        patch_data['start_ang'],
                        patch_data['end_ang']
                    )
                    patches.append(patch)
            
            # Create layer objects
            for layer_data in self.layers_data:
                if layer_data['type'] == 'Straight':
                    layer = StraightLayer(
                        layer_data['material'],
                        layer_data['num_fibers'],
                        layer_data['area_per_fiber'],
                        layer_data['y1'],
                        layer_data['z1'],
                        layer_data['y2'],
                        layer_data['z2']
                    )
                    layers.append(layer)
            
            # Clear and plot
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Use static plotting method
            FiberSection.plot_components(
                fibers=fibers,
                patches=patches,
                layers=layers,
                ax=ax,
                title=f"Preview: {self.name_input.text() or 'Unnamed Section'}"
            )
            
            self.canvas.draw()
            
            # Update info text
            self.update_info_text(fibers, patches, layers)
            
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to update plot: {str(e)}")

    def update_info_text(self, fibers, patches, layers):
        """Update the info text area"""
        total_est_fibers = len(fibers)
        for patch in patches:
            total_est_fibers += patch.estimate_fiber_count()
        for layer in layers:
            total_est_fibers += layer.num_fibers
        
        info = f"""Section Preview Information:

Individual Fibers: {len(fibers)}
Patches: {len(patches)}
Layers: {len(layers)}
Estimated Total Fibers: {total_est_fibers}

Materials Used: {len(set([f.material.user_name for f in fibers] + 
                         [p.material.user_name for p in patches] + 
                         [l.material.user_name for l in layers]))}
"""
        self.info_text.setPlainText(info)

    def load_existing_data(self):
        """Load data from existing fiber section"""
        if not self.fiber_section:
            return
        
        # Load fibers data
        for fiber in self.fiber_section.fibers:
            fiber_data = {
                'y_loc': fiber.y_loc,
                'z_loc': fiber.z_loc,
                'area': fiber.area,
                'material': fiber.material
            }
            self.fibers_data.append(fiber_data)
        
        # Load patches data (simplified - would need full implementation)
        # Load layers data (simplified - would need full implementation)
        
        # Update tables
        self.update_fibers_table()
        self.update_patches_table()
        self.update_layers_table()

    def accept_changes(self):
        """Accept and create the fiber section"""
        try:
            section_name = self.name_input.text().strip()
            if not section_name:
                QMessageBox.warning(self, "Error", "Please enter a section name")
                return
            
            # Validate section has some content
            if (len(self.fibers_data) == 0 and 
                len(self.patches_data) == 0 and 
                len(self.layers_data) == 0):
                QMessageBox.warning(self, "Error", "Section must contain at least one fiber, patch, or layer")
                return
            
            # Create components lists
            components = []
            
            # Create and add fibers
            for fiber_data in self.fibers_data:
                fiber = FiberElement(
                    fiber_data['y_loc'],
                    fiber_data['z_loc'],
                    fiber_data['area'],
                    fiber_data['material']
                )
                components.append(fiber)
            
            # Create and add patches
            for patch_data in self.patches_data:
                if patch_data['type'] == 'Rectangular':
                    patch = RectangularPatch(
                        patch_data['material'],
                        patch_data['num_subdiv_y'],
                        patch_data['num_subdiv_z'],
                        patch_data['y1'],
                        patch_data['z1'],
                        patch_data['y2'],
                        patch_data['z2']
                    )
                    components.append(patch)
                elif patch_data['type'] == 'Quadrilateral':
                    patch = QuadrilateralPatch(
                        patch_data['material'],
                        patch_data['num_subdiv_ij'],
                        patch_data['num_subdiv_jk'],
                        patch_data['vertices']
                    )
                    components.append(patch)
                elif patch_data['type'] == 'Circular':
                    patch = CircularPatch(
                        patch_data['material'],
                        patch_data['num_subdiv_circ'],
                        patch_data['num_subdiv_rad'],
                        patch_data['y_center'],
                        patch_data['z_center'],
                        patch_data['int_rad'],
                        patch_data['ext_rad'],
                        patch_data['start_ang'],
                        patch_data['end_ang']
                    )
                    components.append(patch)
            
            # Create and add layers
            for layer_data in self.layers_data:
                if layer_data['type'] == 'Straight':
                    layer = StraightLayer(
                        layer_data['material'],
                        layer_data['num_fibers'],
                        layer_data['area_per_fiber'],
                        layer_data['y1'],
                        layer_data['z1'],
                        layer_data['y2'],
                        layer_data['z2']
                    )
                    components.append(layer)
            
            # Set GJ if specified
            gj = self.gj_input.value() if self.gj_checkbox.isChecked() else None
            
            # Create the fiber section with all components at once
            if self.is_editing:
                # Update existing section
                self.fiber_section.user_name = section_name
                self.fiber_section.GJ = gj
                self.fiber_section.clear_all()
                # Add components using the new constructor approach
                for component in components:
                    if isinstance(component, FiberElement):
                        self.fiber_section.fibers.append(component)
                    elif hasattr(component, 'get_patch_type'):  # PatchBase
                        self.fiber_section.patches.append(component)
                    elif hasattr(component, 'get_layer_type'):  # LayerBase
                        self.fiber_section.layers.append(component)
                self.created_section = self.fiber_section
            else:
                # Create new section
                self.created_section = FiberSection(
                    user_name=section_name,
                    GJ=gj,
                    components=components
                )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create section: {str(e)}")


# Integration functions for the main section creation dialog
def create_fiber_section_dialog(parent=None):
    """Create a fiber section using the improved dialog"""
    dialog = FiberSectionDialog(parent=parent)
    if dialog.exec() == QDialog.Accepted:
        return dialog.created_section
    return None


def edit_fiber_section_dialog(fiber_section, parent=None):
    """Edit an existing fiber section"""
    dialog = FiberSectionDialog(fiber_section=fiber_section, parent=parent)
    if dialog.exec() == QDialog.Accepted:
        return dialog.created_section
    return None