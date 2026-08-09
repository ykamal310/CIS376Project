import json

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView
)

from app.database import (
    get_user_experiment_results,
    get_user_reservation_history
)


class HistoryWindow(QWidget):
    def __init__(self, user):
        super().__init__()

        self.user = user

        self.setWindowTitle("Results History")
        self.setFixedSize(850, 650)

        title = QLabel(f"History for {user['username']}")

        reservation_title = QLabel("Previous Reservations")

        self.reservation_table = QTableWidget()
        self.reservation_table.setColumnCount(5)

        self.reservation_table.setHorizontalHeaderLabels(
            [
                "Equipment",
                "Date",
                "Start Time",
                "End Time",
                "Status"
            ]
        )

        self.reservation_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.reservation_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        result_title = QLabel("Saved Experiment Results")

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)

        self.result_table.setHorizontalHeaderLabels(
            [
                "Experiment",
                "Result",
                "Saved At",
                "Reservation ID"
            ]
        )

        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        refresh_button = QPushButton("Refresh")
        close_button = QPushButton("Close")

        button_layout = QHBoxLayout()
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(close_button)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(reservation_title)
        layout.addWidget(self.reservation_table)
        layout.addWidget(result_title)
        layout.addWidget(self.result_table)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        refresh_button.clicked.connect(self.load_history)

        close_button.clicked.connect(self.close)

        self.load_history()

    def load_history(self):
        self.load_reservations()
        self.load_results()

    def load_reservations(self):
        reservations = get_user_reservation_history(self.user["id"])

        self.reservation_table.setRowCount(len(reservations))

        for row, reservation in enumerate(reservations):
            values = [
                reservation["equipment_name"],
                reservation["reservation_date"],
                reservation["start_time"],
                reservation["end_time"],
                reservation["status"]
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                self.reservation_table.setItem(row, column, item)

    def load_results(self):
        results = get_user_experiment_results(self.user["id"])

        self.result_table.setRowCount(len(results))

        for row, result in enumerate(results):
            summary = self.get_result_summary(result["result"])

            saved_at = result["created_at"]

            if saved_at:
                saved_at = saved_at.replace("T", " ")
            else:
                saved_at = "Not recorded"

            values = [
                result["experiment_name"],
                summary,
                saved_at,
                result["reservation_id"]
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                self.result_table.setItem(row, column, item)

    def get_result_summary(self, result_text):
        try:
            result_data = json.loads(result_text)

            return result_data.get("summary", result_text)

        except (
            json.JSONDecodeError,
            TypeError
        ):
            return str(result_text)