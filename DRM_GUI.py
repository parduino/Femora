import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                           QVBoxLayout, QHBoxLayout, QSplitter, QFrame,QAction,QToolBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyvistaqt
import code
import io
import contextlib
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
import pyvista as pv

class InteractiveConsole(RichJupyterWidget):
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
        









class LeftPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumWidth(200)
        
        # Add a layout for future widgets
        layout = QVBoxLayout(self)
        layout.addWidget(QWidget())  # Placeholder widget
        
        # Set a background color to make it visible (you can remove this later)
        # self.setStyleSheet("background-color: #f0f0f0;")









class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.font_size = 10  # Initial font size
        self.setWindowTitle("PyVista Plotter with Interactive Python Console")
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
        font = QFont()
        font.setPointSize(self.font_size)
        self.setFont(font)
        self.console.font_size += 1
        
        
    


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()