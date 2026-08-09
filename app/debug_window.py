from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QSpinBox,
    QPushButton,
    QMessageBox
)

from app.database import get_available_equipment
from app.debug_manager import create_debug_session


class DebugWindow(QDialog):
    session_created = pyqtSignal(object)

    def __init__(self, user, parent=None):
        super().__init__(parent)

        self.user = user

        self.setWindowTitle("Debug Session Launcher")

        self.setFixedSize(400, 260)

        title = QLabel("Development Testing Mode")

        self.equipment_combo = QComboBox()

        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 60)
        self.duration_input.setValue(10)
        self.duration_input.setSuffix(" minute(s)")

        launch_button = QPushButton("Launch Debug Session")

        cancel_button = QPushButton("Cancel")

        form = QFormLayout()
        form.addRow("Equipment:", self.equipment_combo)
        form.addRow("Session Duration:", self.duration_input)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(launch_button)
        layout.addWidget(cancel_button)

        self.setLayout(layout)

        launch_button.clicked.connect(self.launch_session)

        cancel_button.clicked.connect(self.reject)

        self.load_equipment()

    def load_equipment(self):
        self.equipment_combo.clear()

        equipment = get_available_equipment()

        for item in equipment:
            self.equipment_combo.addItem(item["name"], item["id"])

        if self.equipment_combo.count() == 0:
            self.equipment_combo.addItem("No equipment available", None)

    def launch_session(self):
        equipment_id = self.equipment_combo.currentData()

        equipment_name = self.equipment_combo.currentText()

        duration_minutes = self.duration_input.value()

        success, result = create_debug_session(
            self.user,
            equipment_id,
            equipment_name,
            duration_minutes
        )

        if not success:
            QMessageBox.warning(self, "Debug Session Error", result)
            return

        self.session_created.emit(result)
        self.accept()