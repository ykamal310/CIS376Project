from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QDateEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView
)

from app.database import (
    get_available_equipment,
    get_time_budget,
    get_user_reservations
)

from app.reservation_manager import (
    get_available_slots,
    create_reservation,
    cancel_user_reservation
)


class ReservationWindow(QWidget):
    def __init__(self, user):
        super().__init__()

        self.user = user

        self.setWindowTitle("Laboratory Reservations")
        self.setFixedSize(750, 600)

        title = QLabel("Laboratory Reservation Management")

        self.remaining_time_label = QLabel()

        self.equipment_combo = QComboBox()

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setMinimumDate(QDate.currentDate())

        self.time_combo = QComboBox()

        create_button = QPushButton("Create Reservation")

        self.reservation_table = QTableWidget()
        self.reservation_table.setColumnCount(6)
        self.reservation_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Equipment",
                "Date",
                "Start Time",
                "End Time",
                "Status"
            ]
        )

        self.reservation_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.reservation_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.reservation_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        cancel_button = QPushButton("Cancel Selected Reservation")
        refresh_button = QPushButton("Refresh")
        close_button = QPushButton("Close")

        equipment_layout = QHBoxLayout()
        equipment_layout.addWidget(QLabel("Equipment:"))
        equipment_layout.addWidget(self.equipment_combo)

        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Reservation Date:"))
        date_layout.addWidget(self.date_input)

        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Available Time:"))
        time_layout.addWidget(self.time_combo)

        button_layout = QHBoxLayout()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(close_button)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.remaining_time_label)
        layout.addLayout(equipment_layout)
        layout.addLayout(date_layout)
        layout.addLayout(time_layout)
        layout.addWidget(create_button)
        layout.addWidget(QLabel("Your Reservations"))
        layout.addWidget(self.reservation_table)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        create_button.clicked.connect(self.create_new_reservation)
        cancel_button.clicked.connect(self.cancel_selected_reservation)
        refresh_button.clicked.connect(self.refresh_window)
        close_button.clicked.connect(self.close)

        self.equipment_combo.currentIndexChanged.connect(
            self.load_available_slots
        )

        self.date_input.dateChanged.connect(
            self.load_available_slots
        )

        self.load_equipment()
        self.refresh_window()

    def load_equipment(self):
        self.equipment_combo.clear()

        equipment = get_available_equipment()

        for item in equipment:
            self.equipment_combo.addItem(
                item["name"],
                item["id"]
            )

        self.load_available_slots()

    def load_available_slots(self):
        self.time_combo.clear()

        equipment_id = self.equipment_combo.currentData()

        if equipment_id is None:
            self.time_combo.addItem("No equipment available")
            self.time_combo.setEnabled(False)
            return

        self.time_combo.setEnabled(True)

        reservation_date = self.date_input.date().toString(
            "yyyy-MM-dd"
        )

        available_slots = get_available_slots(
            equipment_id,
            reservation_date
        )

        if not available_slots:
            self.time_combo.addItem(
                "No available time slots",
                None
            )
            return

        for slot in available_slots:
            slot_text = (
                f"{slot['start_time']} - "
                f"{slot['end_time']}"
            )

            self.time_combo.addItem(
                slot_text,
                (
                    slot["start_time"],
                    slot["end_time"]
                )
            )

    def create_new_reservation(self):
        equipment_id = self.equipment_combo.currentData()
        selected_slot = self.time_combo.currentData()

        if equipment_id is None:
            QMessageBox.warning(
                self,
                "Reservation Error",
                "Select available equipment."
            )
            return

        if selected_slot is None:
            QMessageBox.warning(
                self,
                "Reservation Error",
                "Select an available time slot."
            )
            return

        start_time, end_time = selected_slot

        reservation_date = self.date_input.date().toString(
            "yyyy-MM-dd"
        )

        success, message = create_reservation(
            self.user,
            equipment_id,
            reservation_date,
            start_time,
            end_time
        )

        if success:
            QMessageBox.information(
                self,
                "Reservation Created",
                message
            )

            self.refresh_window()

        else:
            QMessageBox.warning(
                self,
                "Reservation Error",
                message
            )

    def load_reservations(self):
        reservations = get_user_reservations(
            self.user["id"]
        )

        self.reservation_table.setRowCount(
            len(reservations)
        )

        for row, reservation in enumerate(reservations):
            values = [
                reservation["id"],
                reservation["equipment_name"],
                reservation["reservation_date"],
                reservation["start_time"],
                reservation["end_time"],
                reservation["status"]
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                self.reservation_table.setItem(
                    row,
                    column,
                    item
                )

    def load_time_budget(self):
        budget = get_time_budget(
            self.user["id"]
        )

        if not budget:
            self.remaining_time_label.setText(
                "Remaining Weekly Time: Not Available"
            )
            return

        remaining_minutes = max(
            0,
            budget["weekly_minutes"]
            - budget["used_minutes"]
        )

        hours = remaining_minutes // 60
        minutes = remaining_minutes % 60

        self.remaining_time_label.setText(
            f"Remaining Weekly Time: "
            f"{hours} hour(s), {minutes} minute(s)"
        )

    def cancel_selected_reservation(self):
        selected_row = self.reservation_table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "Cancellation Error",
                "Select a reservation first."
            )
            return

        reservation_id = int(
            self.reservation_table.item(
                selected_row,
                0
            ).text()
        )

        confirmation = QMessageBox.question(
            self,
            "Cancel Reservation",
            "Are you sure you want to cancel this reservation?"
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        success, message = cancel_user_reservation(
            self.user,
            reservation_id
        )

        if success:
            QMessageBox.information(
                self,
                "Reservation Cancelled",
                message
            )

            self.refresh_window()

        else:
            QMessageBox.warning(
                self,
                "Cancellation Error",
                message
            )

    def refresh_window(self):
        self.load_reservations()
        self.load_time_budget()
        self.load_available_slots()