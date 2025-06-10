"""
Updated Fiber Section GUI that is compatible with the current FiberSection implementation
Handles Material objects directly and uses the new constructor approach
"""

from qtpy.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
    QDialog, QMessageBox, QGridLayout,
    QTabWidget, QGroupBox, QSpinBox, QDoubleSpinBox, 
    QTextEdit, QSplitter, QCheckBox
)

from femora.components.section.section_opensees import (
    FiberSection, FiberElement,
)
from femora.components.section.section_layer import *
from femora.components.section.section_patch import *
from femora.components.Material.materialBase import Material

# Import GUI utilities
try:
    from .section_gui_utils import (
        setup_material_dropdown, setup_uniaxial_material_dropdown,
        validate_material_selection, get_material_by_combo_selection, 
        set_combo_to_material
    )
except ImportError:
    # Fallback implementations if utilities not available
    def setup_material_dropdown(combo_box, material_filter=None, placeholder_text="Select Material"):
        combo_box.clear()
        combo_box.addItem(placeholder_text, None)
        all_materials = Material.get_all_materials()
        for tag, material in all_materials.items():
            if material_filter and not material_filter(material):
                continue
            display_name = f"{material.user_name} (Tag: {tag}, Type: {material.material_name})"
            combo_box.addItem(display_name, material)
    
    def setup_uniaxial_material_dropdown(combo_box, placeholder_text="Select Uniaxial Material"):
        def is_uniaxial(mat):
            return mat.material_type == 'uniaxialMaterial'
        setup_material_dropdown(combo_box, is_uniaxial, placeholder_text)
    
    def validate_material_selection(combo_box, field_name="Material"):
        material = combo_box.currentData()
        if material is None:
            return False, None, f"Please select a {field_name.lower()}."
        return True, material, ""
    
    def get_material_by_combo_selection(combo_box):
        return combo_box.currentData()
    
    def set_combo_to_material(combo_box, material):
        for i in range(combo_box.count()):
            if combo_box.itemData(i) == material:
                combo_box.setCurrentIndex(i)
                return


class FiberSectionDialog(QDialog):
    """
    Updated dialog for creating and editing fiber sections
    Compatible with the current FiberSection implementation
    """
    
    def __init__(self, fiber_section=None, parent=None):
        super().__init__(parent)
        self.fiber_section = fiber_section
        self.is_editing = fiber_section is not None
        self.created_section = None
        
        self.setWindowTitle("Edit Fiber Section" if self.is_editing else "Create Fiber Section")
        self.setGeometry(200, 200, 1400, 900)
        
        # Data storage for components (collected before creating section)
        self.fibers_data = []
        self.patches_data = []
        self.layers_data = []
        
        self.setup_ui()
        self.connect_signals()
        
        # Load existing data if editing
        if self.is_editing:
            self.load_existing_data()
        
        # Initial plot update
        self.update_preview_plot()

    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Basic section information
        self.setup_basic_info_group(main_layout)
        
        # Create main splitter for content
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side - Component definition tabs
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Create tabs for different component types
        self.tabs = QTabWidget()
        
        # Fibers tab
        self.fibers_tab = self.create_fibers_tab()
        self.tabs.addTab(self.fibers_tab, "Individual Fibers")
        
        # Patches tab
        self.patches_tab = self.create_patches_tab()
        self.tabs.addTab(self.patches_tab, "Patches")
        
        # Layers tab  
        self.layers_tab = self.create_layers_tab()
        self.tabs.addTab(self.layers_tab, "Layers")
        
        left_layout.addWidget(self.tabs)
        
        # Right side - Preview and info
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Matplotlib figure for preview
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        
        preview_group = QGroupBox("Section Preview")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.addWidget(self.canvas)
        
        # Info text area
        info_group = QGroupBox("Section Information")
        info_layout = QVBoxLayout(info_group)
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(150)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        right_layout.addWidget(preview_group)
        right_layout.addWidget(info_group)
        
        # Set splitter sizes (60% left, 40% right)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([840, 560])
        
        # Buttons
        self.setup_buttons(main_layout)

    def setup_basic_info_group(self, parent_layout):
        """Set up the basic section information group"""
        basic_group = QGroupBox("Section Information")
        basic_layout = QGridLayout(basic_group)
        
        # Section name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter section name")
        if self.is_editing:
            self.name_input.setText(self.fiber_section.user_name)
        basic_layout.addWidget(QLabel("Section Name:"), 0, 0)
        basic_layout.addWidget(self.name_input, 0, 1)
        
        # Optional GJ (torsional stiffness)
        self.gj_checkbox = QCheckBox("Specify GJ (Torsional Stiffness)")
        self.gj_input = QDoubleSpinBox()
        self.gj_input.setRange(0.001, 1e12)
        self.gj_input.setDecimals(6)
        self.gj_input.setValue(1.0)
        self.gj_input.setEnabled(False)
        
        self.gj_checkbox.toggled.connect(self.gj_input.setEnabled)
        
        if self.is_editing and self.fiber_section.GJ is not None:
            self.gj_checkbox.setChecked(True)
            self.gj_input.setValue(self.fiber_section.GJ)
        
        basic_layout.addWidget(self.gj_checkbox, 1, 0)
        basic_layout.addWidget(self.gj_input, 1, 1)
        
        parent_layout.addWidget(basic_group)

    def create_fibers_tab(self):
        """Create the individual fibers tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Fiber input group
        input_group = QGroupBox("Add Individual Fiber")
        input_layout = QGridLayout(input_group)
        
        # Coordinate inputs
        self.fiber_y_input = QDoubleSpinBox()
        self.fiber_y_input.setRange(-1e6, 1e6)
        self.fiber_y_input.setDecimals(6)
        
        self.fiber_z_input = QDoubleSpinBox()
        self.fiber_z_input.setRange(-1e6, 1e6)
        self.fiber_z_input.setDecimals(6)
        
        # Area input
        self.fiber_area_input = QDoubleSpinBox()
        self.fiber_area_input.setRange(0.001, 1e6)
        self.fiber_area_input.setDecimals(6)
        self.fiber_area_input.setValue(1.0)
        
        # Material selection
        self.fiber_material_combo = QComboBox()
        setup_uniaxial_material_dropdown(self.fiber_material_combo, "Select Fiber Material")
        
        # Add button
        add_fiber_btn = QPushButton("Add Fiber")
        add_fiber_btn.clicked.connect(self.add_fiber_data)
        
        # Layout inputs
        input_layout.addWidget(QLabel("Y Coordinate:"), 0, 0)
        input_layout.addWidget(self.fiber_y_input, 0, 1)
        input_layout.addWidget(QLabel("Z Coordinate:"), 0, 2)
        input_layout.addWidget(self.fiber_z_input, 0, 3)
        input_layout.addWidget(QLabel("Area:"), 1, 0)
        input_layout.addWidget(self.fiber_area_input, 1, 1)
        input_layout.addWidget(QLabel("Material:"), 1, 2)
        input_layout.addWidget(self.fiber_material_combo, 1, 3)
        input_layout.addWidget(add_fiber_btn, 2, 0, 1, 4)
        
        layout.addWidget(input_group)
        
        # Fibers table
        self.fibers_table = QTableWidget()
        self.fibers_table.setColumnCount(5)
        self.fibers_table.setHorizontalHeaderLabels(["Y", "Z", "Area", "Material", "Actions"])
        self.fibers_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(QLabel("Current Fibers:"))
        layout.addWidget(self.fibers_table)
        
        return tab

    def create_patches_tab(self):
        """Create the patches tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Patch type selection
        patch_type_group = QGroupBox("Patch Type")
        patch_type_layout = QHBoxLayout(patch_type_group)
        
        self.patch_type_combo = QComboBox()
        self.patch_type_combo.addItems(["Rectangular", "Quadrilateral", "Circular"])
        self.patch_type_combo.currentTextChanged.connect(self.on_patch_type_changed)
        
        patch_type_layout.addWidget(QLabel("Patch Type:"))
        patch_type_layout.addWidget(self.patch_type_combo)
        patch_type_layout.addStretch()
        
        layout.addWidget(patch_type_group)
        
        # Stacked widget for different patch input forms
        from qtpy.QtWidgets import QStackedWidget
        self.patch_stack = QStackedWidget()
        
        # Rectangular patch form
        self.rect_patch_form = self.create_rectangular_patch_form()
        self.patch_stack.addWidget(self.rect_patch_form)
        
        # Quadrilateral patch form
        self.quad_patch_form = self.create_quadrilateral_patch_form()
        self.patch_stack.addWidget(self.quad_patch_form)
        
        # Circular patch form
        self.circ_patch_form = self.create_circular_patch_form()
        self.patch_stack.addWidget(self.circ_patch_form)
        
        layout.addWidget(self.patch_stack)
        
        # Patches table
        self.patches_table = QTableWidget()
        self.patches_table.setColumnCount(4)
        self.patches_table.setHorizontalHeaderLabels(["Type", "Material", "Parameters", "Actions"])
        self.patches_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(QLabel("Current Patches:"))
        layout.addWidget(self.patches_table)
        
        return tab

    def create_rectangular_patch_form(self):
        """Create rectangular patch input form"""
        form = QGroupBox("Rectangular Patch Parameters")
        layout = QGridLayout(form)
        
        # Material selection
        self.rect_material_combo = QComboBox()
        setup_uniaxial_material_dropdown(self.rect_material_combo, "Select Material")
        
        # Subdivision inputs
        self.rect_subdiv_y = QSpinBox()
        self.rect_subdiv_y.setRange(1, 100)
        self.rect_subdiv_y.setValue(4)
        
        self.rect_subdiv_z = QSpinBox()
        self.rect_subdiv_z.setRange(1, 100)
        self.rect_subdiv_z.setValue(4)
        
        # Corner coordinates
        self.rect_y1 = QDoubleSpinBox()
        self.rect_y1.setRange(-1e6, 1e6)
        self.rect_y1.setDecimals(6)
        
        self.rect_z1 = QDoubleSpinBox()
        self.rect_z1.setRange(-1e6, 1e6)
        self.rect_z1.setDecimals(6)
        
        self.rect_y2 = QDoubleSpinBox()
        self.rect_y2.setRange(-1e6, 1e6)
        self.rect_y2.setDecimals(6)
        self.rect_y2.setValue(1.0)
        
        self.rect_z2 = QDoubleSpinBox()
        self.rect_z2.setRange(-1e6, 1e6)
        self.rect_z2.setDecimals(6)
        self.rect_z2.setValue(1.0)
        
        # Add button
        add_rect_btn = QPushButton("Add Rectangular Patch")
        add_rect_btn.clicked.connect(self.add_rectangular_patch_data)
        
        # Layout
        layout.addWidget(QLabel("Material:"), 0, 0)
        layout.addWidget(self.rect_material_combo, 0, 1, 1, 3)
        layout.addWidget(QLabel("Y Subdivisions:"), 1, 0)
        layout.addWidget(self.rect_subdiv_y, 1, 1)
        layout.addWidget(QLabel("Z Subdivisions:"), 1, 2)
        layout.addWidget(self.rect_subdiv_z, 1, 3)
        layout.addWidget(QLabel("Corner 1 (Y1, Z1):"), 2, 0)
        layout.addWidget(self.rect_y1, 2, 1)
        layout.addWidget(self.rect_z1, 2, 2)
        layout.addWidget(QLabel("Corner 2 (Y2, Z2):"), 3, 0)
        layout.addWidget(self.rect_y2, 3, 1)
        layout.addWidget(self.rect_z2, 3, 2)
        layout.addWidget(add_rect_btn, 4, 0, 1, 4)
        
        return form

    def create_quadrilateral_patch_form(self):
        """Create quadrilateral patch input form"""
        form = QGroupBox("Quadrilateral Patch Parameters")
        layout = QGridLayout(form)
        
        # Material selection
        self.quad_material_combo = QComboBox()
        setup_uniaxial_material_dropdown(self.quad_material_combo, "Select Material")
        
        # Subdivision inputs
        self.quad_subdiv_y = QSpinBox()
        self.quad_subdiv_y.setRange(1, 100)
        self.quad_subdiv_y.setValue(4)
        
        self.quad_subdiv_z = QSpinBox()
        self.quad_subdiv_z.setRange(1, 100)
        self.quad_subdiv_z.setValue(4)
        
        # Vertex coordinates (I, J, K, L)
        self.quad_vertices = {}
        vertices = ['I', 'J', 'K', 'L']
        
        for i, vertex in enumerate(vertices):
            y_spin = QDoubleSpinBox()
            y_spin.setRange(-1e6, 1e6)
            y_spin.setDecimals(6)
            
            z_spin = QDoubleSpinBox()
            z_spin.setRange(-1e6, 1e6)
            z_spin.setDecimals(6)
            
            self.quad_vertices[vertex] = {'y': y_spin, 'z': z_spin}
        
        # Add button
        add_quad_btn = QPushButton("Add Quadrilateral Patch")
        add_quad_btn.clicked.connect(self.add_quadrilateral_patch_data)
        
        # Layout
        layout.addWidget(QLabel("Material:"), 0, 0)
        layout.addWidget(self.quad_material_combo, 0, 1, 1, 4)
        layout.addWidget(QLabel("Y Subdivisions:"), 1, 0)
        layout.addWidget(self.quad_subdiv_y, 1, 1)
        layout.addWidget(QLabel("Z Subdivisions:"), 1, 2)
        layout.addWidget(self.quad_subdiv_z, 1, 3)
        
        # Vertex inputs
        for i, vertex in enumerate(vertices):
            row = 2 + i
            layout.addWidget(QLabel(f"Vertex {vertex} (Y, Z):"), row, 0)
            layout.addWidget(self.quad_vertices[vertex]['y'], row, 1)
            layout.addWidget(self.quad_vertices[vertex]['z'], row, 2)
        
        layout.addWidget(add_quad_btn, 6, 0, 1, 4)
        
        return form

    def create_circular_patch_form(self):
        """Create circular patch input form"""
        form = QGroupBox("Circular Patch Parameters")
        layout = QGridLayout(form)
        
        # Material selection
        self.circ_material_combo = QComboBox()
        setup_uniaxial_material_dropdown(self.circ_material_combo, "Select Material")
        
        # Subdivision inputs
        self.circ_subdiv_circ = QSpinBox()
        self.circ_subdiv_circ.setRange(1, 100)
        self.circ_subdiv_circ.setValue(8)
        
        self.circ_subdiv_rad = QSpinBox()
        self.circ_subdiv_rad.setRange(1, 100)
        self.circ_subdiv_rad.setValue(4)
        
        # Center coordinates
        self.circ_y_center = QDoubleSpinBox()
        self.circ_y_center.setRange(-1e6, 1e6)
        self.circ_y_center.setDecimals(6)
        
        self.circ_z_center = QDoubleSpinBox()
        self.circ_z_center.setRange(-1e6, 1e6)
        self.circ_z_center.setDecimals(6)
        
        # Radius inputs
        self.circ_inner_radius = QDoubleSpinBox()
        self.circ_inner_radius.setRange(0, 1e6)
        self.circ_inner_radius.setDecimals(6)
        
        self.circ_outer_radius = QDoubleSpinBox()
        self.circ_outer_radius.setRange(0.001, 1e6)
        self.circ_outer_radius.setDecimals(6)
        self.circ_outer_radius.setValue(1.0)
        
        # Angle inputs
        self.circ_start_angle = QDoubleSpinBox()
        self.circ_start_angle.setRange(-360, 360)
        self.circ_start_angle.setDecimals(2)
        self.circ_start_angle.setValue(0)
        
        self.circ_end_angle = QDoubleSpinBox()
        self.circ_end_angle.setRange(-360, 360)
        self.circ_end_angle.setDecimals(2)
        self.circ_end_angle.setValue(360)
        
        # Add button
        add_circ_btn = QPushButton("Add Circular Patch")
        add_circ_btn.clicked.connect(self.add_circular_patch_data)
        
        # Layout
        layout.addWidget(QLabel("Material:"), 0, 0)
        layout.addWidget(self.circ_material_combo, 0, 1, 1, 3)
        layout.addWidget(QLabel("Circumferential Subdivisions:"), 1, 0)
        layout.addWidget(self.circ_subdiv_circ, 1, 1)
        layout.addWidget(QLabel("Radial Subdivisions:"), 1, 2)
        layout.addWidget(self.circ_subdiv_rad, 1, 3)
        layout.addWidget(QLabel("Center Y:"), 2, 0)
        layout.addWidget(self.circ_y_center, 2, 1)
        layout.addWidget(QLabel("Center Z:"), 2, 2)
        layout.addWidget(self.circ_z_center, 2, 3)
        layout.addWidget(QLabel("Inner Radius:"), 3, 0)
        layout.addWidget(self.circ_inner_radius, 3, 1)
        layout.addWidget(QLabel("Outer Radius:"), 3, 2)
        layout.addWidget(self.circ_outer_radius, 3, 3)
        layout.addWidget(QLabel("Start Angle (deg):"), 4, 0)
        layout.addWidget(self.circ_start_angle, 4, 1)
        layout.addWidget(QLabel("End Angle (deg):"), 4, 2)
        layout.addWidget(self.circ_end_angle, 4, 3)
        layout.addWidget(add_circ_btn, 5, 0, 1, 4)
        
        return form

    def create_layers_tab(self):
        """Create the layers tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Layer type selection
        layer_type_group = QGroupBox("Layer Type")
        layer_type_layout = QHBoxLayout(layer_type_group)
        
        self.layer_type_combo = QComboBox()
        self.layer_type_combo.addItems(["Straight", "Circular"])
        self.layer_type_combo.currentTextChanged.connect(self.on_layer_type_changed)
        
        layer_type_layout.addWidget(QLabel("Layer Type:"))
        layer_type_layout.addWidget(self.layer_type_combo)
        layer_type_layout.addStretch()
        
        layout.addWidget(layer_type_group)
        
        # Stacked widget for different layer forms
        from qtpy.QtWidgets import QStackedWidget
        self.layer_stack = QStackedWidget()
        
        # Straight layer form
        self.straight_layer_form = self.create_straight_layer_form()
        self.layer_stack.addWidget(self.straight_layer_form)
        
        # Circular layer form
        self.circular_layer_form = self.create_circular_layer_form()
        self.layer_stack.addWidget(self.circular_layer_form)
        
        layout.addWidget(self.layer_stack)
        
        # Layers table
        self.layers_table = QTableWidget()
        self.layers_table.setColumnCount(4)
        self.layers_table.setHorizontalHeaderLabels(["Type", "Material", "Parameters", "Actions"])
        self.layers_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(QLabel("Current Layers:"))
        layout.addWidget(self.layers_table)
        
        return tab

    def create_straight_layer_form(self):
        """Create straight layer input form"""
        form = QGroupBox("Straight Layer Parameters")
        layout = QGridLayout(form)
        
        # Material selection
        self.straight_material_combo = QComboBox()
        setup_uniaxial_material_dropdown(self.straight_material_combo, "Select Material")
        
        # Number of fibers and area per fiber
        self.straight_num_fibers = QSpinBox()
        self.straight_num_fibers.setRange(1, 1000)
        self.straight_num_fibers.setValue(5)
        
        self.straight_area_per_fiber = QDoubleSpinBox()
        self.straight_area_per_fiber.setRange(0.001, 1e6)
        self.straight_area_per_fiber.setDecimals(6)
        self.straight_area_per_fiber.setValue(0.1)
        
        # Start and end coordinates
        self.straight_y1 = QDoubleSpinBox()
        self.straight_y1.setRange(-1e6, 1e6)
        self.straight_y1.setDecimals(6)
        
        self.straight_z1 = QDoubleSpinBox()
        self.straight_z1.setRange(-1e6, 1e6)
        self.straight_z1.setDecimals(6)
        
        self.straight_y2 = QDoubleSpinBox()
        self.straight_y2.setRange(-1e6, 1e6)
        self.straight_y2.setDecimals(6)
        self.straight_y2.setValue(1.0)
        
        self.straight_z2 = QDoubleSpinBox()
        self.straight_z2.setRange(-1e6, 1e6)
        self.straight_z2.setDecimals(6)
        
        # Add button
        add_straight_btn = QPushButton("Add Straight Layer")
        add_straight_btn.clicked.connect(self.add_straight_layer_data)
        
        # Layout
        layout.addWidget(QLabel("Material:"), 0, 0)
        layout.addWidget(self.straight_material_combo, 0, 1, 1, 3)
        layout.addWidget(QLabel("Number of Fibers:"), 1, 0)
        layout.addWidget(self.straight_num_fibers, 1, 1)
        layout.addWidget(QLabel("Area per Fiber:"), 1, 2)
        layout.addWidget(self.straight_area_per_fiber, 1, 3)
        layout.addWidget(QLabel("Start Point (Y1, Z1):"), 2, 0)
        layout.addWidget(self.straight_y1, 2, 1)
        layout.addWidget(self.straight_z1, 2, 2)
        layout.addWidget(QLabel("End Point (Y2, Z2):"), 3, 0)
        layout.addWidget(self.straight_y2, 3, 1)
        layout.addWidget(self.straight_z2, 3, 2)
        layout.addWidget(add_straight_btn, 4, 0, 1, 4)
        
        return form

    def create_circular_layer_form(self):
        """Create circular layer input form"""
        form = QGroupBox("Circular Layer Parameters")
        layout = QGridLayout(form)
        
        # Material selection
        self.circular_material_combo = QComboBox()
        setup_uniaxial_material_dropdown(self.circular_material_combo, "Select Material")
        
        # Number of fibers and area per fiber
        self.circular_num_fibers = QSpinBox()
        self.circular_num_fibers.setRange(1, 1000)
        self.circular_num_fibers.setValue(8)
        
        self.circular_area_per_fiber = QDoubleSpinBox()
        self.circular_area_per_fiber.setRange(0.001, 1e6)
        self.circular_area_per_fiber.setDecimals(6)
        self.circular_area_per_fiber.setValue(0.1)
        
        # Center coordinates
        self.circular_y_center = QDoubleSpinBox()
        self.circular_y_center.setRange(-1e6, 1e6)
        self.circular_y_center.setDecimals(6)
        
        self.circular_z_center = QDoubleSpinBox()
        self.circular_z_center.setRange(-1e6, 1e6)
        self.circular_z_center.setDecimals(6)
        
        # Radius
        self.circular_radius = QDoubleSpinBox()
        self.circular_radius.setRange(0.001, 1e6)
        self.circular_radius.setDecimals(6)
        self.circular_radius.setValue(1.0)
        
        # Angle range
        self.circular_start_angle = QDoubleSpinBox()
        self.circular_start_angle.setRange(-360, 360)
        self.circular_start_angle.setDecimals(2)
        self.circular_start_angle.setValue(0)
        
        self.circular_end_angle = QDoubleSpinBox()
        self.circular_end_angle.setRange(-360, 360)
        self.circular_end_angle.setDecimals(2)
        self.circular_end_angle.setValue(360)
        
        # Add button
        add_circular_btn = QPushButton("Add Circular Layer")
        add_circular_btn.clicked.connect(self.add_circular_layer_data)
        
        # Layout
        layout.addWidget(QLabel("Material:"), 0, 0)
        layout.addWidget(self.circular_material_combo, 0, 1, 1, 3)
        layout.addWidget(QLabel("Number of Fibers:"), 1, 0)
        layout.addWidget(self.circular_num_fibers, 1, 1)
        layout.addWidget(QLabel("Area per Fiber:"), 1, 2)
        layout.addWidget(self.circular_area_per_fiber, 1, 3)
        layout.addWidget(QLabel("Center Y:"), 2, 0)
        layout.addWidget(self.circular_y_center, 2, 1)
        layout.addWidget(QLabel("Center Z:"), 2, 2)
        layout.addWidget(self.circular_z_center, 2, 3)
        layout.addWidget(QLabel("Radius:"), 3, 0)
        layout.addWidget(self.circular_radius, 3, 1)
        layout.addWidget(QLabel("Start Angle (deg):"), 3, 2)
        layout.addWidget(self.circular_start_angle, 3, 3)
        layout.addWidget(QLabel("End Angle (deg):"), 4, 0)
        layout.addWidget(self.circular_end_angle, 4, 1)
        layout.addWidget(add_circular_btn, 4, 2, 1, 2)
        
        return form

    def setup_buttons(self, parent_layout):
        """Set up dialog buttons"""
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        self.accept_btn = QPushButton("Create Section" if not self.is_editing else "Update Section")
        self.accept_btn.clicked.connect(self.accept_changes)
        self.accept_btn.setDefault(True)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.accept_btn)
        
        parent_layout.addLayout(button_layout)

    def connect_signals(self):
        """Connect UI signals"""
        # Update plot when name changes
        self.name_input.textChanged.connect(self.update_preview_plot)
        
        # Update plot when GJ changes
        self.gj_checkbox.toggled.connect(self.update_preview_plot)
        self.gj_input.valueChanged.connect(self.update_preview_plot)

    def on_patch_type_changed(self, patch_type):
        """Handle patch type selection change"""
        if patch_type == "Rectangular":
            self.patch_stack.setCurrentIndex(0)
        elif patch_type == "Quadrilateral":
            self.patch_stack.setCurrentIndex(1)
        elif patch_type == "Circular":
            self.patch_stack.setCurrentIndex(2)

    def on_layer_type_changed(self, layer_type):
        """Handle layer type selection change"""
        if layer_type == "Straight":
            self.layer_stack.setCurrentIndex(0)
        elif layer_type == "Circular":
            self.layer_stack.setCurrentIndex(1)

    def add_fiber_data(self):
        """Add individual fiber data"""
        try:
            is_valid, material, error_msg = validate_material_selection(
                self.fiber_material_combo, "fiber material"
            )
            if not is_valid:
                QMessageBox.warning(self, "Error", error_msg)
                return
            
            fiber_data = {
                'y_loc': self.fiber_y_input.value(),
                'z_loc': self.fiber_z_input.value(),
                'area': self.fiber_area_input.value(),
                'material': material
            }
            
            self.fibers_data.append(fiber_data)
            self.update_fibers_table()
            self.update_preview_plot()
            
            # Clear inputs for next entry
            self.fiber_y_input.setValue(0)
            self.fiber_z_input.setValue(0)
            self.fiber_area_input.setValue(1.0)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add fiber: {str(e)}")

    def add_rectangular_patch_data(self):
        """Add rectangular patch data"""
        try:
            is_valid, material, error_msg = validate_material_selection(
                self.rect_material_combo, "patch material"
            )
            if not is_valid:
                QMessageBox.warning(self, "Error", error_msg)
                return
            
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
            self.update_preview_plot()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add patch: {str(e)}")

    def add_quadrilateral_patch_data(self):
        """Add quadrilateral patch data"""
        try:
            is_valid, material, error_msg = validate_material_selection(
                self.quad_material_combo, "patch material"
            )
            if not is_valid:
                QMessageBox.warning(self, "Error", error_msg)
                return
            
            # Collect vertices
            vertices = []
            for vertex in ['I', 'J', 'K', 'L']:
                y = self.quad_vertices[vertex]['y'].value()
                z = self.quad_vertices[vertex]['z'].value()
                vertices.append((y, z))
            
            patch_data = {
                'type': 'Quadrilateral',
                'material': material,
                'num_subdiv_y': self.quad_subdiv_y.value(),
                'num_subdiv_z': self.quad_subdiv_z.value(),
                'vertices': vertices
            }
            
            self.patches_data.append(patch_data)
            self.update_patches_table()
            self.update_preview_plot()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add patch: {str(e)}")

    def add_circular_patch_data(self):
        """Add circular patch data"""
        try:
            is_valid, material, error_msg = validate_material_selection(
                self.circ_material_combo, "patch material"
            )
            if not is_valid:
                QMessageBox.warning(self, "Error", error_msg)
                return
            
            patch_data = {
                'type': 'Circular',
                'material': material,
                'num_subdiv_circ': self.circ_subdiv_circ.value(),
                'num_subdiv_rad': self.circ_subdiv_rad.value(),
                'y_center': self.circ_y_center.value(),
                'z_center': self.circ_z_center.value(),
                'inner_radius': self.circ_inner_radius.value(),
                'outer_radius': self.circ_outer_radius.value(),
                'start_angle': self.circ_start_angle.value(),
                'end_angle': self.circ_end_angle.value()
            }
            
            self.patches_data.append(patch_data)
            self.update_patches_table()
            self.update_preview_plot()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add patch: {str(e)}")

    def add_straight_layer_data(self):
        """Add straight layer data"""
        try:
            is_valid, material, error_msg = validate_material_selection(
                self.straight_material_combo, "layer material"
            )
            if not is_valid:
                QMessageBox.warning(self, "Error", error_msg)
                return
            
            layer_data = {
                'type': 'Straight',
                'material': material,
                'num_fibers': self.straight_num_fibers.value(),
                'area_per_fiber': self.straight_area_per_fiber.value(),
                'y1': self.straight_y1.value(),
                'z1': self.straight_z1.value(),
                'y2': self.straight_y2.value(),
                'z2': self.straight_z2.value()
            }
            
            self.layers_data.append(layer_data)
            self.update_layers_table()
            self.update_preview_plot()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add layer: {str(e)}")

    def add_circular_layer_data(self):
        """Add circular layer data"""
        try:
            is_valid, material, error_msg = validate_material_selection(
                self.circular_material_combo, "layer material"
            )
            if not is_valid:
                QMessageBox.warning(self, "Error", error_msg)
                return
            
            layer_data = {
                'type': 'Circular',
                'material': material,
                'num_fibers': self.circular_num_fibers.value(),
                'area_per_fiber': self.circular_area_per_fiber.value(),
                'y_center': self.circular_y_center.value(),
                'z_center': self.circular_z_center.value(),
                'radius': self.circular_radius.value(),
                'start_angle': self.circular_start_angle.value(),
                'end_angle': self.circular_end_angle.value()
            }
            
            self.layers_data.append(layer_data)
            self.update_layers_table()
            self.update_preview_plot()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add layer: {str(e)}")

    def update_fibers_table(self):
        """Update the fibers table display"""
        self.fibers_table.setRowCount(len(self.fibers_data))
        
        for row, fiber_data in enumerate(self.fibers_data):
            self.fibers_table.setItem(row, 0, QTableWidgetItem(f"{fiber_data['y_loc']:.4f}"))
            self.fibers_table.setItem(row, 1, QTableWidgetItem(f"{fiber_data['z_loc']:.4f}"))
            self.fibers_table.setItem(row, 2, QTableWidgetItem(f"{fiber_data['area']:.4f}"))
            self.fibers_table.setItem(row, 3, QTableWidgetItem(fiber_data['material'].user_name))
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_fiber(r))
            self.fibers_table.setCellWidget(row, 4, delete_btn)

    def update_patches_table(self):
        """Update the patches table display"""
        self.patches_table.setRowCount(len(self.patches_data))
        
        for row, patch_data in enumerate(self.patches_data):
            self.patches_table.setItem(row, 0, QTableWidgetItem(patch_data['type']))
            self.patches_table.setItem(row, 1, QTableWidgetItem(patch_data['material'].user_name))
            
            # Create parameter summary
            if patch_data['type'] == 'Rectangular':
                params = f"Subdiv: {patch_data['num_subdiv_y']}x{patch_data['num_subdiv_z']}, " \
                        f"Corners: ({patch_data['y1']:.2f},{patch_data['z1']:.2f}) to " \
                        f"({patch_data['y2']:.2f},{patch_data['z2']:.2f})"
            elif patch_data['type'] == 'Quadrilateral':
                params = f"Subdiv: {patch_data['num_subdiv_y']}x{patch_data['num_subdiv_z']}, " \
                        f"Vertices: {len(patch_data['vertices'])}"
            elif patch_data['type'] == 'Circular':
                params = f"Subdiv: {patch_data['num_subdiv_circ']}x{patch_data['num_subdiv_rad']}, " \
                        f"Center: ({patch_data['y_center']:.2f},{patch_data['z_center']:.2f}), " \
                        f"R: {patch_data['inner_radius']:.2f}-{patch_data['outer_radius']:.2f}"
            
            self.patches_table.setItem(row, 2, QTableWidgetItem(params))
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_patch(r))
            self.patches_table.setCellWidget(row, 3, delete_btn)

    def update_layers_table(self):
        """Update the layers table display"""
        self.layers_table.setRowCount(len(self.layers_data))
        
        for row, layer_data in enumerate(self.layers_data):
            self.layers_table.setItem(row, 0, QTableWidgetItem(layer_data['type']))
            self.layers_table.setItem(row, 1, QTableWidgetItem(layer_data['material'].user_name))
            
            # Create parameter summary
            if layer_data['type'] == 'Straight':
                params = f"Fibers: {layer_data['num_fibers']}, Area: {layer_data['area_per_fiber']:.4f}, " \
                        f"From: ({layer_data['y1']:.2f},{layer_data['z1']:.2f}) to " \
                        f"({layer_data['y2']:.2f},{layer_data['z2']:.2f})"
            elif layer_data['type'] == 'Circular':
                params = f"Fibers: {layer_data['num_fibers']}, Area: {layer_data['area_per_fiber']:.4f}, " \
                        f"Center: ({layer_data['y_center']:.2f},{layer_data['z_center']:.2f}), " \
                        f"R: {layer_data['radius']:.2f}"
            
            self.layers_table.setItem(row, 2, QTableWidgetItem(params))
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_layer(r))
            self.layers_table.setCellWidget(row, 3, delete_btn)

    def delete_fiber(self, row):
        """Delete a fiber from the data"""
        if 0 <= row < len(self.fibers_data):
            self.fibers_data.pop(row)
            self.update_fibers_table()
            self.update_preview_plot()

    def delete_patch(self, row):
        """Delete a patch from the data"""
        if 0 <= row < len(self.patches_data):
            self.patches_data.pop(row)
            self.update_patches_table()
            self.update_preview_plot()

    def delete_layer(self, row):
        """Delete a layer from the data"""
        if 0 <= row < len(self.layers_data):
            self.layers_data.pop(row)
            self.update_layers_table()
            self.update_preview_plot()

    def update_preview_plot(self):
        """Update the section preview plot"""
        try:
            # Create temporary component objects for plotting
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
                    vertices = patch_data['vertices']
                    patch = QuadrilateralPatch(
                        patch_data['material'],
                        patch_data['num_subdiv_y'],
                        patch_data['num_subdiv_z'],
                        vertices[0][0], vertices[0][1],  # I
                        vertices[1][0], vertices[1][1],  # J
                        vertices[2][0], vertices[2][1],  # K
                        vertices[3][0], vertices[3][1]   # L
                    )
                    patches.append(patch)
                elif patch_data['type'] == 'Circular':
                    patch = CircularPatch(
                        patch_data['material'],
                        patch_data['num_subdiv_circ'],
                        patch_data['num_subdiv_rad'],
                        patch_data['y_center'],
                        patch_data['z_center'],
                        patch_data['inner_radius'],
                        patch_data['outer_radius'],
                        patch_data['start_angle'],
                        patch_data['end_angle']
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
                elif layer_data['type'] == 'Circular':
                    layer = CircularLayer(
                        layer_data['material'],
                        layer_data['num_fibers'],
                        layer_data['area_per_fiber'],
                        layer_data['y_center'],
                        layer_data['z_center'],
                        layer_data['radius'],
                        layer_data['start_angle'],
                        layer_data['end_angle']
                    )
                    layers.append(layer)
            
            # Clear and plot
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Use static plotting method from FiberSection
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
            # Clear plot on error
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f"Plot Error:\n{str(e)}", 
                   ha='center', va='center', transform=ax.transAxes)
            self.canvas.draw()

    def update_info_text(self, fibers, patches, layers):
        """Update the section information display"""
        total_est_fibers = len(fibers)
        for patch in patches:
            total_est_fibers += patch.estimate_fiber_count()
        for layer in layers:
            total_est_fibers += layer.num_fibers
        
        # Count unique materials
        all_materials = set()
        for f in fibers:
            all_materials.add(f.material.user_name)
        for p in patches:
            all_materials.add(p.material.user_name)
        for l in layers:
            all_materials.add(l.material.user_name)
        
        info = f"""Section Preview Information:

Individual Fibers: {len(fibers)}
Patches: {len(patches)}
Layers: {len(layers)}
Estimated Total Fibers: {total_est_fibers}

Materials Used: {len(all_materials)}
Material Names: {', '.join(sorted(all_materials)) if all_materials else 'None'}

GJ (Torsional Stiffness): {'Specified' if self.gj_checkbox.isChecked() else 'Not specified'}
"""
        self.info_text.setPlainText(info)

    def load_existing_data(self):
        """Load data from existing fiber section for editing"""
        if not self.fiber_section:
            return
        
        # Load individual fibers
        for fiber in self.fiber_section.fibers:
            fiber_data = {
                'y_loc': fiber.y_loc,
                'z_loc': fiber.z_loc,
                'area': fiber.area,
                'material': fiber.material
            }
            self.fibers_data.append(fiber_data)
        
        # Load patches - this would need to be expanded based on how patch data is stored
        # For now, we'll leave this as a placeholder since the exact storage format
        # depends on the implementation details
        
        # Load layers - similar placeholder
        
        # Update tables
        self.update_fibers_table()
        self.update_patches_table()
        self.update_layers_table()

    def accept_changes(self):
        """Create or update the fiber section"""
        try:
            section_name = self.name_input.text().strip()
            if not section_name:
                QMessageBox.warning(self, "Error", "Please enter a section name")
                return
            
            # Validate section has some content
            if (len(self.fibers_data) == 0 and 
                len(self.patches_data) == 0 and 
                len(self.layers_data) == 0):
                QMessageBox.warning(self, "Error", "Section must have at least one fiber, patch, or layer")
                return
            
            # Create component objects
            components = []
            
            # Add individual fibers
            for fiber_data in self.fibers_data:
                fiber = FiberElement(
                    fiber_data['y_loc'],
                    fiber_data['z_loc'],
                    fiber_data['area'],
                    fiber_data['material']
                )
                components.append(fiber)
            
            # Add patches
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
                    vertices = patch_data['vertices']
                    patch = QuadrilateralPatch(
                        patch_data['material'],
                        patch_data['num_subdiv_y'],
                        patch_data['num_subdiv_z'],
                        vertices[0][0], vertices[0][1],  # I
                        vertices[1][0], vertices[1][1],  # J
                        vertices[2][0], vertices[2][1],  # K
                        vertices[3][0], vertices[3][1]   # L
                    )
                    components.append(patch)
                elif patch_data['type'] == 'Circular':
                    patch = CircularPatch(
                        patch_data['material'],
                        patch_data['num_subdiv_circ'],
                        patch_data['num_subdiv_rad'],
                        patch_data['y_center'],
                        patch_data['z_center'],
                        patch_data['inner_radius'],
                        patch_data['outer_radius'],
                        patch_data['start_angle'],
                        patch_data['end_angle']
                    )
                    components.append(patch)
            
            # Add layers
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
                elif layer_data['type'] == 'Circular':
                    layer = CircularLayer(
                        layer_data['material'],
                        layer_data['num_fibers'],
                        layer_data['area_per_fiber'],
                        layer_data['y_center'],
                        layer_data['z_center'],
                        layer_data['radius'],
                        layer_data['start_angle'],
                        layer_data['end_angle']
                    )
                    components.append(layer)
            
            # Set GJ if specified
            gj = self.gj_input.value() if self.gj_checkbox.isChecked() else None
            
            # Create or update the fiber section
            if self.is_editing:
                # For editing, we would need to implement an update method
                # or recreate the section. For now, create a new one.
                self.created_section = FiberSection(
                    user_name=section_name,
                    GJ=gj,
                    components=components
                )
            else:
                # Create new section using the updated constructor
                self.created_section = FiberSection(
                    user_name=section_name,
                    GJ=gj,
                    components=components
                )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create section: {str(e)}")


# Integration functions for the main application
def create_fiber_section_dialog(parent=None):
    """Create a new fiber section using the dialog"""
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


if __name__ == "__main__":
    # Test the dialog
    from qtpy.QtWidgets import QApplication
    import sys
    from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial, ElasticUniaxialMaterial
    elas1 = ElasticUniaxialMaterial(user_name="Steel", E=210e9, nu=0.3)
    elas2 = ElasticUniaxialMaterial(user_name="Concrete", E=30e9, nu=0.2)


    app = QApplication(sys.argv)
    
    # Create some test materials if needed
    # This would typically be done through the material manager
    
    dialog = FiberSectionDialog()
    dialog.show()
    
    sys.exit(app.exec())