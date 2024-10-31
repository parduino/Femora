import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                           QVBoxLayout, QHBoxLayout, QSplitter, QFrame,QAction)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyvistaqt
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
import pyvista as pv

from Soil import SoilBlocks
from PyQt5.QtWidgets import QTabWidget, QLabel
from Styles import AppStyles

# =================================================================================================
# Interactive console
# =================================================================================================
class InteractiveConsole(RichJupyterWidget):
    '''
    A console widget that can execute Python code and display rich output.
    '''
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create kernel manager and kernel
        kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        
        # Create kernel client
        kernel_client = kernel_manager.client()
        kernel_client.start_channels()
        
        # Set up the console with the kernel
        self.kernel_manager = kernel_manager
        self.kernel_client = kernel_client
        
        # Configure appearance
        self.syntax_style = 'solarized-dark'
        self.set_default_style(colors='linux')
        

# =================================================================================================
# Left panel
# =================================================================================================

class LeftPanel(QFrame):
    '''
    A simple frame that will be used as the left panel of the main window.
    '''
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumWidth(200)
        
        # Add a layout for future widgets
        layout = QVBoxLayout(self)

        # create different tabs with names soil, DRM, Absorbing, Analysis, Partition
        # Create a tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs
        self.material_tab  = QWidget()
        self.soil_tab      = QWidget()
        self.drm_tab       = QWidget()
        self.absorbing_tab = QWidget()
        self.analysis_tab  = QWidget()
        self.partition_tab = QWidget()

        # Add tabs to the tab widget
        self.tabs.addTab(self.material_tab, "Material")
        self.tabs.addTab(self.soil_tab, "Soil")
        self.tabs.addTab(self.drm_tab, "DRM")
        self.tabs.addTab(self.absorbing_tab, "Absorbing")
        self.tabs.addTab(self.partition_tab, "Partition")
        self.tabs.addTab(self.analysis_tab, "Analysis")

        # Optionally, add some content to each tab
        self.soil_tab.layout = QVBoxLayout()
        self.soil_tab.layout.addWidget(SoilBlocks())
        self.soil_tab.setLayout(self.soil_tab.layout)

        self.drm_tab.layout = QVBoxLayout()
        self.drm_tab.layout.addWidget(QLabel("DRM content here"))
        self.drm_tab.setLayout(self.drm_tab.layout)

        self.absorbing_tab.layout = QVBoxLayout()
        self.absorbing_tab.layout.addWidget(QLabel("Absorbing content here"))
        self.absorbing_tab.setLayout(self.absorbing_tab.layout)

        self.analysis_tab.layout = QVBoxLayout()
        self.analysis_tab.layout.addWidget(QLabel("Analysis content here"))
        self.analysis_tab.setLayout(self.analysis_tab.layout)

        self.partition_tab.layout = QVBoxLayout()
        self.partition_tab.layout.addWidget(QLabel("Partition content here"))
        self.partition_tab.setLayout(self.partition_tab.layout)

    
        
# =================================================================================================
# Main window
# =================================================================================================

class MainWindow(QMainWindow):
    '''
    Main window of the application that contains the plotter and the console and left panel.
    '''
    def __init__(self):
        super().__init__()
        self.font_size = 10  # Initial font size
        self.setWindowTitle("PyVista Plotter with Interactive Python Console")

        self.setStyleSheet(AppStyles.COMBINED_STYLE)

        self.resize(1400, 800)
  
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Create main horizontal splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Create left panel
        self.left_panel = LeftPanel()
        
        # Create right panel with vertical splitter
        self.right_panel = QSplitter(Qt.Vertical)
        
        # Add panels to main splitter
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.right_panel)
        
        # Set up plotter
        self.plotter = pyvistaqt.BackgroundPlotter(show=False)
        self.plotter_widget = self.plotter.app_window
        self.plotter_widget.setMinimumHeight(400)
        
        # Set up console
        self.console = InteractiveConsole()
        self.console.setMinimumHeight(200)
        
        # Add plotter and console to right splitter
        self.right_panel.addWidget(self.plotter_widget)
        self.right_panel.addWidget(self.console)
        
        # Set initial splitter sizes
        self.main_splitter.setSizes([300, 1100])  # Left panel : Right panel ratio
        self.right_panel.setSizes([600, 200])     # Plotter : Console ratio
        
        self.create_menu_and_toolbar()
        
        # Make plotter available in console namespace
        self.console.kernel_manager.kernel.shell.push({
            'plotter': self.plotter,
            'pv': pv
        })
        self.showMaximized()


    def create_menu_and_toolbar(self):
        # Create menu bar and add 'Increase Size' and 'Decrease Size' actions
        menubar = self.menuBar()
        file_menu = menubar.addMenu("View")
        
        increase_size_action = QAction("Increase Size", self)
        increase_size_action.setShortcut("Ctrl+=")  # Use Ctrl + = for increasing size
        increase_size_action.triggered.connect(self.increase_font_size)
        file_menu.addAction(increase_size_action)

        decrease_size_action = QAction("Decrease Size", self)
        decrease_size_action.setShortcut("Ctrl+-")  # Use Ctrl + - for decreasing size
        decrease_size_action.triggered.connect(self.decrease_font_size)
        file_menu.addAction(decrease_size_action)

    def increase_font_size(self):
        self.font_size += 1  # Increase font size by 2
        self.console.change_font_size(+1)
        self.update_font_and_resize()

    def decrease_font_size(self):
        if self.font_size > 6:  # Limit the minimum font size
            self.font_size -= 1  # Decrease font size by 2
            self.console.change_font_size(-1)
            self.update_font_and_resize()


    def update_font_and_resize(self):
        # Update font for the main window
        font = QFont()
        font.setPointSize(self.font_size)
        self.setFont(font)
        
        # Update the entire application style with new font size
        self.setStyleSheet(AppStyles.get_dynamic_style(self.font_size))
        
        # Force update of the UI
        self.update()
        

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()