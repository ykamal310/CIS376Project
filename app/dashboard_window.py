from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox
)

from app.admin_window import AdminWindow
from app.config import DEBUG_MODE
from app.debug_window import DebugWindow
from app.experiment_window import ExperimentWindow
from app.history_window import HistoryWindow
from app.reservation_window import ReservationWindow
from app.session_manager import begin_session


class DashboardWindow(QWidget):
    logged_out = pyqtSignal()

    def __init__(self, user):
        super().__init__()

        self.user = user

        self.reservation_window = None
        self.experiment_window = None
        self.history_window = None
        self.admin_window = None

        self.setWindowTitle("Remote Lab Dashboard")
        self.setFixedSize(400, 400)

        title = QLabel("Remote Laboratory Platform")
        welcome = QLabel(
            f"Welcome, {user['username']}"
        )
        role = QLabel(
            f"Role: {user['role']}"
        )

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(welcome)
        layout.addWidget(role)

        if user["role"] == "Administrator":
            admin_button = QPushButton(
                "Administrator Tools"
            )

            layout.addWidget(admin_button)

            admin_button.clicked.connect(
                self.open_admin_tools
            )

        else:
            reservation_button = QPushButton(
                "Reservations"
            )

            experiment_button = QPushButton(
                "Experiments"
            )

            history_button = QPushButton(
                "Results History"
            )

            layout.addWidget(reservation_button)
            layout.addWidget(experiment_button)
            layout.addWidget(history_button)

            reservation_button.clicked.connect(
                self.open_reservations
            )

            experiment_button.clicked.connect(
                self.open_experiment
            )

            history_button.clicked.connect(
                self.open_history
            )

            if DEBUG_MODE:
                debug_button = QPushButton(
                    "Debug: Launch Test Session"
                )

                layout.addWidget(debug_button)

                debug_button.clicked.connect(
                    self.open_debug_window
                )

        logout_button = QPushButton("Log Out")
        layout.addWidget(logout_button)

        logout_button.clicked.connect(
            self.logout
        )

        self.setLayout(layout)

    def open_reservations(self):
        if (
            self.reservation_window
            and self.reservation_window.isVisible()
        ):
            self.reservation_window.raise_()
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

        self.launch_experiment_window(result)

    def open_debug_window(self):
        if (
            self.experiment_window
            and self.experiment_window.isVisible()
        ):
            QMessageBox.warning(
                self,
                "Session Already Open",
                "Close the current session first."
            )
            return

        window = DebugWindow(
            self.user,
            self
        )

        window.session_created.connect(
            self.launch_experiment_window
        )

        window.exec()

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
            return

        self.history_window = HistoryWindow(
            self.user
        )

        self.history_window.show()

    def open_admin_tools(self):
        if self.user["role"] != "Administrator":
            QMessageBox.warning(
                self,
                "Access Denied",
                "Administrator access is required."
            )
            return

        if (
            self.admin_window
            and self.admin_window.isVisible()
        ):
            self.admin_window.raise_()
            return

        self.admin_window = AdminWindow(
            self.user
        )

        self.admin_window.show()

    def logout(self):
        if self.reservation_window:
            self.reservation_window.close()

        if self.experiment_window:
            self.experiment_window.close()

        if self.history_window:
            self.history_window.close()

        if self.admin_window:
            self.admin_window.close()

        self.logged_out.emit()
        self.close()