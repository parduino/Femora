from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QLabel, QTabWidget
)
from femora.components.transformation.transformation import GeometricTransformation2D, GeometricTransformation3D

class TransformationWidget2D(QWidget):
    """
    Widget for creating a 2D geometric transformation object.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        form = QFormLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Linear", "PDelta", "Corotational"])
        form.addRow(QLabel("Type:"), self.type_combo)
        self.d_xi = QDoubleSpinBox(); self.d_xi.setRange(-1e6, 1e6)
        self.d_yi = QDoubleSpinBox(); self.d_yi.setRange(-1e6, 1e6)
        self.d_xj = QDoubleSpinBox(); self.d_xj.setRange(-1e6, 1e6)
        self.d_yj = QDoubleSpinBox(); self.d_yj.setRange(-1e6, 1e6)
        form.addRow("dXi:", self.d_xi)
        form.addRow("dYi:", self.d_yi)
        form.addRow("dXj:", self.d_xj)
        form.addRow("dYj:", self.d_yj)
        self.layout().addLayout(form)

    def get_transformation(self):
        return GeometricTransformation2D(
            self.type_combo.currentText(),
            self.d_xi.value(),
            self.d_yi.value(),
            self.d_xj.value(),
            self.d_yj.value()
        )

class TransformationWidget3D(QWidget):
    """
    Widget for creating a 3D geometric transformation object.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        form = QFormLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Linear", "PDelta", "Corotational"])
        form.addRow(QLabel("Type:"), self.type_combo)
        self.vecxz_x = QDoubleSpinBox(); self.vecxz_x.setRange(-1e6, 1e6); self.vecxz_x.setValue(0)
        self.vecxz_y = QDoubleSpinBox(); self.vecxz_y.setRange(-1e6, 1e6); self.vecxz_y.setValue(0)
        self.vecxz_z = QDoubleSpinBox(); self.vecxz_z.setRange(-1e6, 1e6); self.vecxz_z.setValue(-1)
        self.d_xi = QDoubleSpinBox(); self.d_xi.setRange(-1e6, 1e6)
        self.d_yi = QDoubleSpinBox(); self.d_yi.setRange(-1e6, 1e6)
        self.d_zi = QDoubleSpinBox(); self.d_zi.setRange(-1e6, 1e6)
        self.d_xj = QDoubleSpinBox(); self.d_xj.setRange(-1e6, 1e6)
        self.d_yj = QDoubleSpinBox(); self.d_yj.setRange(-1e6, 1e6)
        self.d_zj = QDoubleSpinBox(); self.d_zj.setRange(-1e6, 1e6)
        form.addRow("vecXZ X:", self.vecxz_x)
        form.addRow("vecXZ Y:", self.vecxz_y)
        form.addRow("vecXZ Z:", self.vecxz_z)
        form.addRow("dXi:", self.d_xi)
        form.addRow("dYi:", self.d_yi)
        form.addRow("dZi:", self.d_zi)
        form.addRow("dXj:", self.d_xj)
        form.addRow("dYj:", self.d_yj)
        form.addRow("dZj:", self.d_zj)
        self.layout().addLayout(form)

    def get_transformation(self):
        return GeometricTransformation3D(
            self.type_combo.currentText(),
            self.vecxz_x.value(),
            self.vecxz_y.value(),
            self.vecxz_z.value(),
            self.d_xi.value(),
            self.d_yi.value(),
            self.d_zi.value(),
            self.d_xj.value(),
            self.d_yj.value(),
            self.d_zj.value()
        )

# Optionally, you can keep the following demo for manual testing:
if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    tabs = QTabWidget()
    tabs.addTab(TransformationWidget2D(), "2D Transformation")
    tabs.addTab(TransformationWidget3D(), "3D Transformation")
    tabs.show()
    sys.exit(app.exec_())