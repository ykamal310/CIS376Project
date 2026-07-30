from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton
)

from app.reservation_window import ReservationWindow


class DashboardWindow(QWidget):
    logged_out = pyqtSignal()

    def __init__(self, user):
        super().__init__()

        self.user = user
        self.reservation_window = None

        self.setWindowTitle("Remote Lab Dashboard")
        self.setFixedSize(400, 350)

        title = QLabel("Remote Laboratory Platform")
        welcome = QLabel(f"Welcome, {user['username']}")
        role = QLabel(f"Role: {user['role']}")

        reservations_button = QPushButton("Reservations")
        experiments_button = QPushButton("Experiments")
        history_button = QPushButton("Results History")
        logout_button = QPushButton("Log Out")

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(welcome)
        layout.addWidget(role)
        layout.addWidget(reservations_button)
        layout.addWidget(experiments_button)
        layout.addWidget(history_button)
        layout.addWidget(logout_button)

        self.setLayout(layout)

        reservations_button.clicked.connect(
            self.open_reservations
        )

        logout_button.clicked.connect(self.logout)

    def open_reservations(self):
        self.reservation_window = ReservationWindow(
            self.user
        )

        self.reservation_window.show()

    def logout(self):
        if self.reservation_window:
            self.reservation_window.close()

        self.logged_out.emit()
        self.close()