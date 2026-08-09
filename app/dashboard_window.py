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

from app.database import (
    get_next_reservation,
    get_time_budget,
    get_all_reservations,
    get_all_equipment,
    get_all_users
)


class DashboardWindow(QWidget):
    logged_out = pyqtSignal()

    def __init__(self, user):
        super().__init__()

        self.user = user

        self.reservation_window = None
        self.experiment_window = None
        self.history_window = None
        self.admin_window = None

        self.setWindowTitle(
            "Remote Lab Dashboard"
        )

        self.setFixedSize(
            420,
            450
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

        layout = QVBoxLayout()

        layout.addWidget(title)
        layout.addWidget(welcome)
        layout.addWidget(role)

        if user["role"] == "Administrator":
            self.admin_reservation_label = QLabel()
            self.admin_equipment_label = QLabel()
            self.admin_users_label = QLabel()

            layout.addWidget(
                self.admin_reservation_label
            )

            layout.addWidget(
                self.admin_equipment_label
            )

            layout.addWidget(
                self.admin_users_label
            )

            admin_button = QPushButton(
                "Administrator Tools"
            )

            refresh_button = QPushButton(
                "Refresh Overview"
            )

            layout.addWidget(
                admin_button
            )

            layout.addWidget(
                refresh_button
            )

            admin_button.clicked.connect(
                self.open_admin_tools
            )

            refresh_button.clicked.connect(
                self.refresh_admin_dashboard
            )

            self.refresh_admin_dashboard()

        else:
            self.next_reservation_label = QLabel()
            self.time_label = QLabel()

            layout.addWidget(
                self.next_reservation_label
            )

            layout.addWidget(
                self.time_label
            )

            reservation_button = QPushButton(
                "Reservations"
            )

            experiment_button = QPushButton(
                "Experiments"
            )

            history_button = QPushButton(
                "Results History"
            )

            refresh_button = QPushButton(
                "Refresh Dashboard"
            )

            layout.addWidget(
                reservation_button
            )

            layout.addWidget(
                experiment_button
            )

            layout.addWidget(
                history_button
            )

            layout.addWidget(
                refresh_button
            )

            reservation_button.clicked.connect(
                self.open_reservations
            )

            experiment_button.clicked.connect(
                self.open_experiment
            )

            history_button.clicked.connect(
                self.open_history
            )

            refresh_button.clicked.connect(
                self.refresh_student_dashboard
            )

            if DEBUG_MODE:
                debug_button = QPushButton(
                    "Debug: Launch Test Session"
                )

                layout.addWidget(
                    debug_button
                )

                debug_button.clicked.connect(
                    self.open_debug_window
                )

            self.refresh_student_dashboard()

        logout_button = QPushButton(
            "Log Out"
        )

        layout.addWidget(
            logout_button
        )

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

    def launch_experiment_window(
        self,
        session
    ):
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

    def refresh_student_dashboard(self):
        if self.user["role"] != "Student":
            return

        reservation = get_next_reservation(
            self.user["id"]
        )

        if reservation:
            self.next_reservation_label.setText(
                (
                    "Next Reservation: "
                    f"{reservation['equipment_name']} - "
                    f"{reservation['reservation_date']} "
                    f"{reservation['start_time']}"
                )
            )

        else:
            self.next_reservation_label.setText(
                "Next Reservation: None"
            )

        budget = get_time_budget(
            self.user["id"]
        )

        if budget:
            remaining = max(
                0,
                budget["weekly_minutes"]
                - budget["used_minutes"]
            )

            hours = remaining // 60
            minutes = remaining % 60

            self.time_label.setText(
                (
                    "Remaining Weekly Time: "
                    f"{hours}h {minutes}m"
                )
            )

        else:
            self.time_label.setText(
                "Remaining Weekly Time: Not Available"
            )

    def refresh_admin_dashboard(self):
        if self.user["role"] != "Administrator":
            return

        reservations = get_all_reservations()
        equipment = get_all_equipment()
        users = get_all_users()

        scheduled = 0

        for reservation in reservations:
            if reservation["status"] == "Scheduled":
                scheduled += 1

        available = 0

        for item in equipment:
            if item["status"] == "Available":
                available += 1

        self.admin_reservation_label.setText(
            f"Scheduled Reservations: {scheduled}"
        )

        self.admin_equipment_label.setText(
            (
                "Equipment Available: "
                f"{available} / {len(equipment)}"
            )
        )

        self.admin_users_label.setText(
            f"Registered Users: {len(users)}"
        )

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