from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox
)

from app.config import DEBUG_MODE
from app.debug_window import DebugWindow
from app.experiment_window import ExperimentWindow
from app.reservation_window import ReservationWindow
from app.session_manager import begin_session

from app.history_window import HistoryWindow


class DashboardWindow(QWidget):
    logged_out = pyqtSignal()

    def __init__(self, user):
        super().__init__()

        self.user = user

        self.reservation_window = None
        self.experiment_window = None
        self.history_window = None

        self.setWindowTitle(
            "Remote Lab Dashboard"
        )

        self.setFixedSize(
            400,
            400
        )

        title = QLabel(
            "Remote Laboratory Platform"
        )

        welcome = QLabel(
            f"Welcome, {user['username']}"
        )

        role = QLabel(
            f"Role: {user['role']}"
        )

        reservations_button = QPushButton(
            "Reservations"
        )

        experiments_button = QPushButton(
            "Experiments"
        )

        history_button = QPushButton(
            "Results History"
        )

        logout_button = QPushButton(
            "Log Out"
        )

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(welcome)
        layout.addWidget(role)
        layout.addWidget(reservations_button)
        layout.addWidget(experiments_button)
        layout.addWidget(history_button)

        if (
            DEBUG_MODE
            and user["role"] == "Student"
        ):
            debug_button = QPushButton(
                "Debug test session"
            )

            layout.addWidget(debug_button)

            debug_button.clicked.connect(
                self.open_debug_window
            )

        layout.addWidget(logout_button)

        self.setLayout(layout)

        reservations_button.clicked.connect(
            self.open_reservations
    )

        experiments_button.clicked.connect(
            self.open_experiment
)

        history_button.clicked.connect(
            self.open_history
            )

        logout_button.clicked.connect(
            self.logout
     )

    def open_reservations(self):
        if (
            self.reservation_window
            and self.reservation_window.isVisible()
        ):
            self.reservation_window.raise_()
            self.reservation_window.activateWindow()
            return

        self.reservation_window = ReservationWindow(
            self.user
        )

        self.reservation_window.show()

    def open_experiment(self):
        if (
            self.experiment_window
            and self.experiment_window.isVisible()
        ):
            self.experiment_window.raise_()
            self.experiment_window.activateWindow()
            return

        success, result = begin_session(
            self.user
        )

        if not success:
            QMessageBox.warning(
                self,
                "Session Access Denied",
                result
            )
            return

        self.launch_experiment_window(
            result
        )

    def open_debug_window(self):
        if (
            self.experiment_window
            and self.experiment_window.isVisible()
        ):
            QMessageBox.warning(
                self,
                "Session Already Open",
                (
                    "Close the current laboratory session "
                    "before starting another one."
                )
            )
            return

        debug_window = DebugWindow(
            self.user,
            self
        )

        debug_window.session_created.connect(
            self.launch_experiment_window
        )

        debug_window.exec()

    def launch_experiment_window(self, session):
        self.experiment_window = ExperimentWindow(
            self.user,
            session
        )

        self.experiment_window.show()

    def open_history(self):
        if (
            self.history_window
            and self.history_window.isVisible()
        ):
            self.history_window.raise_()
            self.history_window.activateWindow()
            return

        self.history_window = HistoryWindow(
            self.user
        )

        self.history_window.show()

    def logout(self):
        if self.reservation_window:
            self.reservation_window.close()

        if self.experiment_window:
            self.experiment_window.close()

        if self.history_window:
            self.history_window.close()

        self.logged_out.emit()
        self.close()