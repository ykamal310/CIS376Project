from datetime import datetime

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox
)

from app.session_manager import finish_session


class ExperimentWindow(QWidget):
    def __init__(self, user, session):
        super().__init__()

        self.user = user
        self.session = session
        self.session_finished = False

        self.setWindowTitle("Active Laboratory Session")
        self.setFixedSize(450, 300)

        title = QLabel("Remote Laboratory Session")

        student_label = QLabel(
            f"Student: {user['username']}"
        )

        equipment_label = QLabel(
            f"Equipment: {session['equipment_name']}"
        )

        reservation_label = QLabel(
            (
                f"Reservation: "
                f"{session['reservation_date']} "
                f"{session['start_time']} - "
                f"{session['end_time']}"
            )
        )

        self.remaining_time_label = QLabel()

        status_label = QLabel(
            "Session access is active."
        )

        experiment_label = QLabel(
            "Simulated experiment controls will be added next."
        )

        end_button = QPushButton("End Session")

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(student_label)
        layout.addWidget(equipment_label)
        layout.addWidget(reservation_label)
        layout.addWidget(self.remaining_time_label)
        layout.addWidget(status_label)
        layout.addWidget(experiment_label)
        layout.addWidget(end_button)

        self.setLayout(layout)

        end_button.clicked.connect(
            self.end_session_early
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.update_remaining_time
        )

        self.timer.start(1000)

        self.update_remaining_time()

    def get_reservation_end(self):
        return datetime.strptime(
            (
                f"{self.session['reservation_date']} "
                f"{self.session['end_time']}"
            ),
            "%Y-%m-%d %H:%M"
        )

    def update_remaining_time(self):
        reservation_end = self.get_reservation_end()

        remaining_seconds = int(
            (
                reservation_end
                - datetime.now()
            ).total_seconds()
        )

        if remaining_seconds <= 0:
            self.timer.stop()

            self.finish_current_session(
                reservation_expired=True
            )

            QMessageBox.information(
                self,
                "Session Ended",
                (
                    "The reservation period has expired. "
                    "Laboratory access has ended."
                )
            )

            self.close()
            return

        hours = remaining_seconds // 3600

        minutes = (
            remaining_seconds % 3600
        ) // 60

        seconds = remaining_seconds % 60

        self.remaining_time_label.setText(
            (
                f"Remaining Time: "
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )
        )

    def end_session_early(self):
        confirmation = QMessageBox.question(
            self,
            "End Session",
            "Are you sure you want to end this session?"
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        self.finish_current_session()
        self.close()

    def finish_current_session(
        self,
        reservation_expired=False
    ):
        if self.session_finished:
            return

        finish_session(
            self.session["session_id"],
            self.session["reservation_id"],
            reservation_expired
        )

        self.session_finished = True

    def closeEvent(self, event):
        self.timer.stop()
        self.finish_current_session()
        event.accept()