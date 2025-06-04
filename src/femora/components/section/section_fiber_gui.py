"""
Comprehensive GUI components for Fiber Section creation and editing
Supports all fiber section features: individual fibers, patches, layers, and GJ parameter
"""

from qtpy.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
    QDialog, QFormLayout, QMessageBox, QHeaderView, QGridLayout,
    QTabWidget, QGroupBox, QSpinBox, QDoubleSpinBox, QTextEdit,
    QFrame, QSplitter, QListWidget, QListWidgetItem, QCheckBox,QFileDialog
)


from femora.components.section.section_opensees import (
    FiberSection, FiberElement, RectangularPatch, QuadrilateralPatch, 
    CircularPatch, StraightLayer
)
from femora.components.Material.materialBase import Material


class FiberSectionPlotWidget(QWidget):
    """
    Widget for plotting fiber sections with interactive controls
    """
    
    def __init__(self, fiber_section, parent=None):
        super().__init__(parent)
        self.fiber_section = fiber_section
        
        self.setWindowTitle(f"Fiber Section Plot: {fiber_section.user_name}")
        self.setGeometry(300, 300, 1000, 700)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Plot area
        self.setup_plot_area(main_layout)
        
        # Control panel
        self.setup_control_panel(main_layout)
        
        # Initial plot
        self.update_plot()
    
    def setup_plot_area(self, main_layout):
        """Setup the matplotlib plot area"""
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        plot_layout.addWidget(self.canvas)
        
        # Plot control buttons
        plot_buttons = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh Plot")
        refresh_btn.clicked.connect(self.update_plot)
        plot_buttons.addWidget(refresh_btn)
        
        save_btn = QPushButton("Save Plot")
        save_btn.clicked.connect(self.save_plot)
        plot_buttons.addWidget(save_btn)
        
        plot_buttons.addStretch()
        plot_layout.addLayout(plot_buttons)
        
        main_layout.addWidget(plot_widget, stretch=3)
    
    def setup_control_panel(self, main_layout):
        """Setup the control panel for plot options"""
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # Visibility controls
        visibility_group = QGroupBox("Visibility Options")
        visibility_layout = QVBoxLayout(visibility_group)
        
        self.show_fibers_check = QCheckBox("Show Individual Fibers")
        self.show_fibers_check.setChecked(True)
        self.show_fibers_check.toggled.connect(self.update_plot)
        visibility_layout.addWidget(self.show_fibers_check)
        
        self.show_patches_check = QCheckBox("Show Patches")
        self.show_patches_check.setChecked(True)
        self.show_patches_check.toggled.connect(self.update_plot)
        visibility_layout.addWidget(self.show_patches_check)
        
        self.show_layers_check = QCheckBox("Show Layers")
        self.show_layers_check.setChecked(True)
        self.show_layers_check.toggled.connect(self.update_plot)
        visibility_layout.addWidget(self.show_layers_check)
        
        self.show_patch_outline_check = QCheckBox("Show Patch Outlines")
        self.show_patch_outline_check.setChecked(True)
        self.show_patch_outline_check.toggled.connect(self.update_plot)
        visibility_layout.addWidget(self.show_patch_outline_check)
        
        self.show_fiber_grid_check = QCheckBox("Show Fiber Grid in Patches")
        self.show_fiber_grid_check.setChecked(False)
        self.show_fiber_grid_check.toggled.connect(self.update_plot)
        visibility_layout.addWidget(self.show_fiber_grid_check)
        
        self.show_layer_line_check = QCheckBox("Show Layer Lines")
        self.show_layer_line_check.setChecked(True)
        self.show_layer_line_check.toggled.connect(self.update_plot)
        visibility_layout.addWidget(self.show_layer_line_check)
        
        control_layout.addWidget(visibility_group)
        
        # Plot customization
        custom_group = QGroupBox("Plot Customization")
        custom_layout = QFormLayout(custom_group)
        
        self.title_input = QLineEdit(f"Fiber Section: {self.fiber_section.user_name}")
        custom_layout.addRow("Title:", self.title_input)
        
        control_layout.addWidget(custom_group)
        
        # Section information
        info_group = QGroupBox("Section Information")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(200)
        self.update_section_info()
        info_layout.addWidget(self.info_text)
        
        control_layout.addWidget(info_group)
        
        control_layout.addStretch()
        
        main_layout.addWidget(control_panel, stretch=1)
    
    def update_plot(self):
        """Update the plot with current settings"""
        try:
            # Clear the current plot
            self.ax.clear()
            
            # Get plot options
            show_fibers = self.show_fibers_check.isChecked()
            show_patches = self.show_patches_check.isChecked()
            show_layers = self.show_layers_check.isChecked()
            show_patch_outline = self.show_patch_outline_check.isChecked()
            show_fiber_grid = self.show_fiber_grid_check.isChecked()
            show_layer_line = self.show_layer_line_check.isChecked()
            title = self.title_input.text()
            
            # Plot the fiber section
            self.fiber_section.plot(
                ax=self.ax,
                show_fibers=show_fibers,
                show_patches=show_patches,
                show_layers=show_layers,
                show_patch_outline=show_patch_outline,
                show_fiber_grid=show_fiber_grid,
                show_layer_line=show_layer_line,
                title=title
            )
            
            # Refresh the canvas
            self.canvas.draw()
            
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to update plot: {str(e)}")
    
    def save_plot(self):
        """Save the current plot to file"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Plot", 
                f"fiber_section_{self.fiber_section.user_name}.png",
                "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)"
            )
            
            if file_path:
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Success", f"Plot saved to: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save plot: {str(e)}")
    
    def update_section_info(self):
        """Update the section information display"""
        summary = self.fiber_section.get_section_summary()
        
        info_text = f"""
        Section Summary:
            Name: {self.fiber_section.user_name}
            Tag: {self.fiber_section.tag}

            Components:
            • Individual Fibers: {summary['individual_fibers']}
            • Patches: {summary['patches']}
            • Layers: {summary['layers']}

            Estimated Total Fibers: {summary['estimated_total_fibers']}

            Materials Used:
            {chr(10).join('• ' + mat for mat in summary['materials_used']) if summary['materials_used'] else '• None'}

            Torsional Stiffness: {'Yes' if summary['has_torsional_stiffness'] else 'No'}

            Patch Types: {', '.join(summary['patch_types']) if summary['patch_types'] else 'None'}
            Layer Types: {', '.join(summary['layer_types']) if summary['layer_types'] else 'None'}
        """
        
        self.info_text.setPlainText(info_text)


class FiberSectionDialog(QDialog):
    """
    Comprehensive dialog for creating and editing fiber sections
    """
    
    def __init__(self, fiber_section=None, parent=None):
        super().__init__(parent)
        self.fiber_section = fiber_section
        self.is_editing = fiber_section is not None
        
        self.setWindowTitle("Edit Fiber Section" if self.is_editing else "Create Fiber Section")
        self.setGeometry(200, 200, 600, 400)
        
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
        """Setup main content area with tabs including plot tab"""
        self.tab_widget = QTabWidget()
        
        # Individual Fibers tab
        self.setup_fibers_tab()
        
        # Patches tab
        self.setup_patches_tab()
        
        # Layers tab  
        self.setup_layers_tab()
        
        # Summary tab
        self.setup_summary_tab()
        
        # Plot tab (new)
        self.setup_plot_tab()
        
        main_layout.addWidget(self.tab_widget)

    def setup_plot_tab(self):
        """Setup plot tab for visualization"""
        plot_widget = QWidget()
        layout = QVBoxLayout(plot_widget)
        
        # Plot button and controls
        plot_controls = QHBoxLayout()
        
        self.plot_section_btn = QPushButton("Plot Section")
        self.plot_section_btn.clicked.connect(self.plot_section)
        plot_controls.addWidget(self.plot_section_btn)
        
        self.open_plot_window_btn = QPushButton("Open Plot Window")
        self.open_plot_window_btn.clicked.connect(self.open_plot_window)
        plot_controls.addWidget(self.open_plot_window_btn)
        
        plot_controls.addStretch()
        layout.addLayout(plot_controls)
        
        # Embedded plot area
        self.plot_frame = QFrame()
        self.plot_frame.setFrameStyle(QFrame.StyledPanel)
        self.plot_frame.setMinimumHeight(400)
        
        # Create matplotlib figure for embedded plot
        self.embedded_figure = Figure(figsize=(8, 6))
        self.embedded_canvas = FigureCanvas(self.embedded_figure)
        
        plot_frame_layout = QVBoxLayout(self.plot_frame)
        plot_frame_layout.addWidget(self.embedded_canvas)
        
        layout.addWidget(self.plot_frame)
        
        # Plot status
        self.plot_status_label = QLabel("No plot generated yet. Click 'Plot Section' to visualize.")
        layout.addWidget(self.plot_status_label)
        
        self.tab_widget.addTab(plot_widget, "Plot")

    def plot_section(self):
        """Plot the section in the embedded canvas"""
        try:
            if not self.fiber_section:
                # Create temporary section for plotting
                self.create_temp_section()
            
            if not self.fiber_section:
                QMessageBox.warning(self, "No Section", "Please create section components before plotting.")
                return
            
            # Clear the embedded plot
            self.embedded_figure.clear()
            ax = self.embedded_figure.add_subplot(111)
            
            # Plot the section
            self.fiber_section.plot(ax=ax)
            
            # Refresh the canvas
            self.embedded_canvas.draw()
            
            self.plot_status_label.setText("Section plotted successfully.")
            
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to plot section: {str(e)}")
            self.plot_status_label.setText(f"Plot error: {str(e)}")

    def open_plot_window(self):
        """Open dedicated plot window"""
        try:
            if not self.fiber_section:
                self.create_temp_section()
            
            if not self.fiber_section:
                QMessageBox.warning(self, "No Section", "Please create section components before plotting.")
                return
            
            # Open plot widget in separate window
            self.plot_window = FiberSectionPlotWidget(self.fiber_section, self)
            self.plot_window.show()
            
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to open plot window: {str(e)}")


    def create_temp_section(self):
        """Create temporary section for plotting if one doesn't exist"""
        if not self.fiber_section:
            section_name = self.name_input.text().strip() or "Temp_Section"
            
            # Create section with GJ if specified
            gj = self.gj_input.value() if self.gj_checkbox.isChecked() else None
            self.fiber_section = FiberSection(section_name, GJ=gj)



    # Include all the original methods from FiberSectionDialog
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




    def setup_fibers_tab(self):
        """Setup tab for individual fiber management"""
        fibers_widget = QWidget()
        layout = QHBoxLayout(fibers_widget)
        
        # Left side - fiber list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        left_layout.addWidget(QLabel("Individual Fibers:"))
        
        self.fibers_list = QListWidget()
        left_layout.addWidget(self.fibers_list)
        
        # Fiber control buttons
        fiber_buttons = QHBoxLayout()
        add_fiber_btn = QPushButton("Add Fiber")
        edit_fiber_btn = QPushButton("Edit Fiber")
        remove_fiber_btn = QPushButton("Remove Fiber")
        
        add_fiber_btn.clicked.connect(self.add_fiber)
        edit_fiber_btn.clicked.connect(self.edit_fiber)
        remove_fiber_btn.clicked.connect(self.remove_fiber)
        
        fiber_buttons.addWidget(add_fiber_btn)
        fiber_buttons.addWidget(edit_fiber_btn)
        fiber_buttons.addWidget(remove_fiber_btn)
        left_layout.addLayout(fiber_buttons)
        
        layout.addWidget(left_panel)
        
        # Right side - fiber creation/editing form
        right_panel = QGroupBox("Fiber Properties")
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
        
        # Left side - patch list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        left_layout.addWidget(QLabel("Patches:"))
        
        self.patches_list = QListWidget()
        left_layout.addWidget(self.patches_list)
        
        # Patch control buttons
        patch_buttons = QHBoxLayout()
        add_patch_btn = QPushButton("Add Patch")
        edit_patch_btn = QPushButton("Edit Patch")
        remove_patch_btn = QPushButton("Remove Patch")
        
        add_patch_btn.clicked.connect(self.add_patch)
        edit_patch_btn.clicked.connect(self.edit_patch)
        remove_patch_btn.clicked.connect(self.remove_patch)
        
        patch_buttons.addWidget(add_patch_btn)
        patch_buttons.addWidget(edit_patch_btn)
        patch_buttons.addWidget(remove_patch_btn)
        left_layout.addLayout(patch_buttons)
        
        patch_content.addWidget(left_panel)
        
        # Right side - patch creation forms (stacked)
        self.patch_forms_widget = QWidget()
        self.patch_forms_layout = QVBoxLayout(self.patch_forms_widget)
        
        self.setup_rectangular_patch_form()
        self.setup_quadrilateral_patch_form()
        self.setup_circular_patch_form()
        
        patch_content.addWidget(self.patch_forms_widget)
        layout.addLayout(patch_content)
        
        self.tab_widget.addTab(patches_widget, "Patches")

    def setup_rectangular_patch_form(self):
        """Setup form for rectangular patches"""
        self.rect_patch_form = QGroupBox("Rectangular Patch Properties")
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
        
        self.patch_forms_layout.addWidget(self.rect_patch_form)

    def setup_quadrilateral_patch_form(self):
        """Setup form for quadrilateral patches"""
        self.quad_patch_form = QGroupBox("Quadrilateral Patch Properties")
        layout = QFormLayout(self.quad_patch_form)
        
        self.quad_material_combo = QComboBox()
        layout.addRow("Material:", self.quad_material_combo)
        
        self.quad_subdiv_ij = QSpinBox()
        self.quad_subdiv_ij.setRange(1, 1000)
        self.quad_subdiv_ij.setValue(10)
        layout.addRow("I-J Subdivisions:", self.quad_subdiv_ij)
        
        self.quad_subdiv_jk = QSpinBox()
        self.quad_subdiv_jk.setRange(1, 1000)
        self.quad_subdiv_jk.setValue(10)
        layout.addRow("J-K Subdivisions:", self.quad_subdiv_jk)
        
        # Vertices (I, J, K, L)
        vertices_group = QGroupBox("Vertices (Counter-clockwise)")
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
        
        layout.addRow(vertices_group)
        
        self.quad_patch_form.setVisible(False)
        self.patch_forms_layout.addWidget(self.quad_patch_form)

    def setup_circular_patch_form(self):
        """Setup form for circular patches"""
        self.circ_patch_form = QGroupBox("Circular Patch Properties")
        layout = QFormLayout(self.circ_patch_form)
        
        self.circ_material_combo = QComboBox()
        layout.addRow("Material:", self.circ_material_combo)
        
        self.circ_subdiv_circ = QSpinBox()
        self.circ_subdiv_circ.setRange(1, 1000)
        self.circ_subdiv_circ.setValue(16)
        layout.addRow("Circumferential Subdivisions:", self.circ_subdiv_circ)
        
        self.circ_subdiv_rad = QSpinBox()
        self.circ_subdiv_rad.setRange(1, 1000)
        self.circ_subdiv_rad.setValue(4)
        layout.addRow("Radial Subdivisions:", self.circ_subdiv_rad)
        
        self.circ_y_center = QDoubleSpinBox()
        self.circ_y_center.setRange(-1e6, 1e6)
        self.circ_y_center.setDecimals(6)
        layout.addRow("Y Center:", self.circ_y_center)
        
        self.circ_z_center = QDoubleSpinBox()
        self.circ_z_center.setRange(-1e6, 1e6)
        self.circ_z_center.setDecimals(6)
        layout.addRow("Z Center:", self.circ_z_center)
        
        self.circ_int_rad = QDoubleSpinBox()
        self.circ_int_rad.setRange(0.0, 1e6)
        self.circ_int_rad.setDecimals(6)
        layout.addRow("Inner Radius:", self.circ_int_rad)
        
        self.circ_ext_rad = QDoubleSpinBox()
        self.circ_ext_rad.setRange(0.001, 1e6)
        self.circ_ext_rad.setDecimals(6)
        layout.addRow("Outer Radius:", self.circ_ext_rad)
        
        # Optional angle parameters
        self.circ_use_angles = QCheckBox("Specify Custom Angles")
        layout.addRow(self.circ_use_angles)
        
        self.circ_start_ang = QDoubleSpinBox()
        self.circ_start_ang.setRange(0, 360)
        self.circ_start_ang.setDecimals(1)
        self.circ_start_ang.setValue(0)
        self.circ_start_ang.setEnabled(False)
        layout.addRow("Start Angle (deg):", self.circ_start_ang)
        
        self.circ_end_ang = QDoubleSpinBox()
        self.circ_end_ang.setRange(0, 360)
        self.circ_end_ang.setDecimals(1)
        self.circ_end_ang.setValue(360)
        self.circ_end_ang.setEnabled(False)
        layout.addRow("End Angle (deg):", self.circ_end_ang)
        
        self.circ_use_angles.toggled.connect(self.circ_start_ang.setEnabled)
        self.circ_use_angles.toggled.connect(self.circ_end_ang.setEnabled)
        
        self.circ_patch_form.setVisible(False)
        self.patch_forms_layout.addWidget(self.circ_patch_form)

    def setup_layers_tab(self):
        """Setup tab for layer management"""
        layers_widget = QWidget()
        layout = QHBoxLayout(layers_widget)
        
        # Left side - layer list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        left_layout.addWidget(QLabel("Layers:"))
        
        self.layers_list = QListWidget()
        left_layout.addWidget(self.layers_list)
        
        # Layer control buttons
        layer_buttons = QHBoxLayout()
        add_layer_btn = QPushButton("Add Layer")
        edit_layer_btn = QPushButton("Edit Layer")
        remove_layer_btn = QPushButton("Remove Layer")
        
        add_layer_btn.clicked.connect(self.add_layer)
        edit_layer_btn.clicked.connect(self.edit_layer)
        remove_layer_btn.clicked.connect(self.remove_layer)
        
        layer_buttons.addWidget(add_layer_btn)
        layer_buttons.addWidget(edit_layer_btn)
        layer_buttons.addWidget(remove_layer_btn)
        left_layout.addLayout(layer_buttons)
        
        layout.addWidget(left_panel)
        
        # Right side - layer creation form
        right_panel = QGroupBox("Straight Layer Properties")
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
        
        layout.addWidget(right_panel)
        
        self.tab_widget.addTab(layers_widget, "Layers")

    def setup_summary_tab(self):
        """Setup summary tab showing section overview"""
        summary_widget = QWidget()
        layout = QVBoxLayout(summary_widget)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        layout.addWidget(QLabel("Section Summary:"))
        layout.addWidget(self.summary_text)
        
        # Update summary button
        update_summary_btn = QPushButton("Update Summary")
        update_summary_btn.clicked.connect(self.update_summary)
        layout.addWidget(update_summary_btn)
        
        self.tab_widget.addTab(summary_widget, "Summary")

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
        
        # Clear all combo boxes
        for combo in [self.fiber_material_combo, self.rect_material_combo, 
                     self.quad_material_combo, self.circ_material_combo, 
                     self.layer_material_combo]:
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

    def add_fiber(self):
        """Add individual fiber to the section"""
        try:
            y_loc = self.fiber_y_input.value()
            z_loc = self.fiber_z_input.value()
            area = self.fiber_area_input.value()
            material = self.fiber_material_combo.currentData()
            
            if material is None:
                QMessageBox.warning(self, "Error", "Please select a material")
                return
            
            # Create temporary fiber section if not editing
            if not self.fiber_section:
                self.fiber_section = FiberSection("temp")
            
            self.fiber_section.add_fiber(y_loc, z_loc, area, material)
            self.update_fibers_list()
            
            # Clear inputs
            self.fiber_y_input.setValue(0)
            self.fiber_z_input.setValue(0)
            self.fiber_area_input.setValue(0)
            self.fiber_material_combo.setCurrentIndex(0)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add fiber: {str(e)}")

    def add_patch(self):
        """Add patch to the section based on current patch type"""
        try:
            patch_type = self.patch_type_combo.currentText()
            
            # Create temporary fiber section if not editing
            if not self.fiber_section:
                self.fiber_section = FiberSection("temp")
            
            if patch_type == "Rectangular":
                self.add_rectangular_patch()
            elif patch_type == "Quadrilateral":
                self.add_quadrilateral_patch()
            elif patch_type == "Circular":
                self.add_circular_patch()
            
            self.update_patches_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add patch: {str(e)}")

    def add_rectangular_patch(self):
        """Add rectangular patch"""
        material = self.rect_material_combo.currentData()
        if material is None:
            raise ValueError("Please select a material")
        
        self.fiber_section.add_rectangular_patch(
            material=material,
            num_subdiv_y=self.rect_subdiv_y.value(),
            num_subdiv_z=self.rect_subdiv_z.value(),
            y1=self.rect_y1.value(),
            z1=self.rect_z1.value(),
            y2=self.rect_y2.value(),
            z2=self.rect_z2.value()
        )

    def add_quadrilateral_patch(self):
        """Add quadrilateral patch"""
        material = self.quad_material_combo.currentData()
        if material is None:
            raise ValueError("Please select a material")
        
        vertices = []
        for vertex in ['I', 'J', 'K', 'L']:
            y = self.quad_vertices[vertex]['y'].value()
            z = self.quad_vertices[vertex]['z'].value()
            vertices.append((y, z))
        
        self.fiber_section.add_quadrilateral_patch(
            material=material,
            num_subdiv_ij=self.quad_subdiv_ij.value(),
            num_subdiv_jk=self.quad_subdiv_jk.value(),
            vertices=vertices
        )

    def add_circular_patch(self):
        """Add circular patch"""
        material = self.circ_material_combo.currentData()
        if material is None:
            raise ValueError("Please select a material")
        
        start_ang = self.circ_start_ang.value() if self.circ_use_angles.isChecked() else None
        end_ang = self.circ_end_ang.value() if self.circ_use_angles.isChecked() else None
        
        self.fiber_section.add_circular_patch(
            material=material,
            num_subdiv_circ=self.circ_subdiv_circ.value(),
            num_subdiv_rad=self.circ_subdiv_rad.value(),
            y_center=self.circ_y_center.value(),
            z_center=self.circ_z_center.value(),
            int_rad=self.circ_int_rad.value(),
            ext_rad=self.circ_ext_rad.value(),
            start_ang=start_ang,
            end_ang=end_ang
        )

    def add_layer(self):
        """Add layer to the section"""
        try:
            material = self.layer_material_combo.currentData()
            if material is None:
                QMessageBox.warning(self, "Error", "Please select a material")
                return
            
            # Create temporary fiber section if not editing
            if not self.fiber_section:
                self.fiber_section = FiberSection("temp")
            
            self.fiber_section.add_straight_layer(
                material=material,
                num_fibers=self.layer_num_fibers.value(),
                area_per_fiber=self.layer_area_per_fiber.value(),
                y1=self.layer_y1.value(),
                z1=self.layer_z1.value(),
                y2=self.layer_y2.value(),
                z2=self.layer_z2.value()
            )
            
            self.update_layers_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add layer: {str(e)}")

    def edit_fiber(self):
        """Edit selected fiber"""
        current_item = self.fibers_list.currentItem()
        if current_item is None:
            QMessageBox.warning(self, "Error", "Please select a fiber to edit")
            return
        
        # Implementation for editing would go here
        QMessageBox.information(self, "Edit Fiber", "Fiber editing functionality to be implemented")

    def edit_patch(self):
        """Edit selected patch"""
        current_item = self.patches_list.currentItem()
        if current_item is None:
            QMessageBox.warning(self, "Error", "Please select a patch to edit")
            return
        
        QMessageBox.information(self, "Edit Patch", "Patch editing functionality to be implemented")

    def edit_layer(self):
        """Edit selected layer"""
        current_item = self.layers_list.currentItem()
        if current_item is None:
            QMessageBox.warning(self, "Error", "Please select a layer to edit")
            return
        
        QMessageBox.information(self, "Edit Layer", "Layer editing functionality to be implemented")

    def remove_fiber(self):
        """Remove selected fiber"""
        current_row = self.fibers_list.currentRow()
        if current_row >= 0 and self.fiber_section:
            del self.fiber_section.fibers[current_row]
            self.update_fibers_list()

    def remove_patch(self):
        """Remove selected patch"""
        current_row = self.patches_list.currentRow()
        if current_row >= 0 and self.fiber_section:
            del self.fiber_section.patches[current_row]
            self.update_patches_list()

    def remove_layer(self):
        """Remove selected layer"""
        current_row = self.layers_list.currentRow()
        if current_row >= 0 and self.fiber_section:
            del self.fiber_section.layers[current_row]
            self.update_layers_list()

    def update_fibers_list(self):
        """Update the fibers list display"""
        self.fibers_list.clear()
        if self.fiber_section:
            for i, fiber in enumerate(self.fiber_section.fibers):
                item_text = f"Fiber {i+1}: ({fiber.y_loc}, {fiber.z_loc}), A={fiber.area}, Mat={fiber.material.user_name}"
                self.fibers_list.addItem(item_text)

    def update_patches_list(self):
        """Update the patches list display"""
        self.patches_list.clear()
        if self.fiber_section:
            for i, patch in enumerate(self.fiber_section.patches):
                item_text = f"Patch {i+1}: {patch.get_patch_type()}, {patch.estimate_fiber_count()} fibers, Mat={patch.material.user_name}"
                self.patches_list.addItem(item_text)

    def update_layers_list(self):
        """Update the layers list display"""
        self.layers_list.clear()
        if self.fiber_section:
            for i, layer in enumerate(self.fiber_section.layers):
                item_text = f"Layer {i+1}: {layer.get_layer_type()}, {layer.num_fibers} fibers, Mat={layer.material.user_name}"
                self.layers_list.addItem(item_text)

    def update_summary(self):
        """Update the summary text"""
        if not self.fiber_section:
            self.summary_text.setPlainText("No fiber section data")
            return
        
        summary = self.fiber_section.get_section_summary()
        
        text = f"""Fiber Section Summary:
        
Name: {self.fiber_section.user_name}
Tag: {self.fiber_section.tag}

Components:
- Individual Fibers: {summary['individual_fibers']}
- Patches: {summary['patches']} ({', '.join(summary['patch_types']) if summary['patch_types'] else 'None'})
- Layers: {summary['layers']} ({', '.join(summary['layer_types']) if summary['layer_types'] else 'None'})

Estimated Total Fibers: {summary['estimated_total_fibers']}

Materials Used: {', '.join(summary['materials_used']) if summary['materials_used'] else 'None'}

Torsional Stiffness: {'Yes' if summary['has_torsional_stiffness'] else 'No'}

OpenSees TCL Command:
{self.fiber_section.to_tcl()}
"""
        
        self.summary_text.setPlainText(text)

    def load_existing_data(self):
        """Load data from existing fiber section"""
        if not self.fiber_section:
            return
        
        # Update lists
        self.update_fibers_list()
        self.update_patches_list()
        self.update_layers_list()
        self.update_summary()

    def accept_changes(self):
        """Accept and validate changes"""
        try:
            section_name = self.name_input.text().strip()
            if not section_name:
                QMessageBox.warning(self, "Error", "Please enter a section name")
                return
            
            # Create or update fiber section
            if not self.fiber_section:
                self.fiber_section = FiberSection(section_name)
            else:
                self.fiber_section.user_name = section_name
            
            # Set GJ if specified
            if self.gj_checkbox.isChecked():
                self.fiber_section.GJ = self.gj_input.value()
            else:
                self.fiber_section.GJ = None
            
            # Validate section has some content
            if (len(self.fiber_section.fibers) == 0 and 
                len(self.fiber_section.patches) == 0 and 
                len(self.fiber_section.layers) == 0):
                QMessageBox.warning(self, "Error", "Section must contain at least one fiber, patch, or layer")
                return
            
            self.created_section = self.fiber_section
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create section: {str(e)}")


# Integration with main section creation dialog
def create_fiber_section_dialog(parent=None):
    """Create a fiber section using the specialized dialog"""
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