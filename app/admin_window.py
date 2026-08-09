from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QTabWidget,
    QSpinBox,
    QDialog,
    QFormLayout,
    QComboBox,
    QDateEdit
)

from PyQt6.QtCore import QDate

from app.database import (
    get_all_equipment,
    get_all_reservations,
    get_all_users,
    get_reservation_for_admin
)

from app.admin_manager import (
    change_equipment_status,
    cancel_admin_reservation,
    change_user_role,
    add_student_time,
    modify_admin_reservation
)

from app.reservation_manager import TIME_SLOTS


class AdminReservationDialog(QDialog):
    def __init__(self, reservation, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Modify Reservation")
        self.setFixedSize(350, 250)

        self.equipment_combo = QComboBox()

        equipment = get_all_equipment()

        for item in equipment:
            self.equipment_combo.addItem(item["name"], item["id"])

            if item["id"] == reservation["equipment_id"]:
                self.equipment_combo.setCurrentIndex(self.equipment_combo.count() - 1)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setMinimumDate(QDate.currentDate())

        old_date = QDate.fromString(reservation["reservation_date"], "yyyy-MM-dd")

        self.date_input.setDate(old_date)

        self.time_combo = QComboBox()

        for start, end in TIME_SLOTS:
            text = f"{start} - {end}"

            self.time_combo.addItem(text, (start, end))

            if start == reservation["start_time"]:
                self.time_combo.setCurrentIndex(self.time_combo.count() - 1)

        save_button = QPushButton("Save Changes")

        cancel_button = QPushButton("Cancel")

        form = QFormLayout()

        form.addRow("Equipment:", self.equipment_combo)

        form.addRow("Date:", self.date_input)

        form.addRow("Time:", self.time_combo)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)

        self.setLayout(layout)

        save_button.clicked.connect(self.accept)

        cancel_button.clicked.connect(self.reject)


class AdminWindow(QWidget):
    def __init__(self, user):
        super().__init__()

        self.user = user

        self.setWindowTitle("Administrator Tools")
        self.setFixedSize(900, 600)

        title = QLabel(f"Administrator: {user['username']}")

        tabs = QTabWidget()

        equipment_tab = QWidget()
        reservation_tab = QWidget()
        user_tab = QWidget()

        tabs.addTab(equipment_tab, "Equipment")

        tabs.addTab(reservation_tab, "Reservations")

        tabs.addTab(user_tab, "Users")

        self.setup_equipment_tab(equipment_tab)

        self.setup_reservation_tab(reservation_tab)

        self.setup_user_tab(user_tab)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(tabs)
        layout.addWidget(close_button)

        self.setLayout(layout)

        self.load_equipment()
        self.load_reservations()
        self.load_users()

    def setup_equipment_tab(self, tab):
        self.equipment_table = QTableWidget()
        self.equipment_table.setColumnCount(3)

        self.equipment_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Equipment",
                "Status"
            ]
        )

        self.equipment_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.equipment_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.equipment_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        toggle_button = QPushButton("Change Selected Status")

        refresh_button = QPushButton("Refresh Equipment")

        toggle_button.clicked.connect(self.toggle_equipment)

        refresh_button.clicked.connect(self.load_equipment)

        buttons = QHBoxLayout()
        buttons.addWidget(toggle_button)
        buttons.addWidget(refresh_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Laboratory Equipment"))
        layout.addWidget(self.equipment_table)
        layout.addLayout(buttons)

        tab.setLayout(layout)

    def setup_reservation_tab(self, tab):
        self.reservation_table = QTableWidget()
        self.reservation_table.setColumnCount(7)

        self.reservation_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Student",
                "Equipment",
                "Date",
                "Start",
                "End",
                "Status"
            ]
        )

        self.reservation_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.reservation_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.reservation_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        modify_button = QPushButton("Modify Selected Reservation")
        cancel_button = QPushButton("Cancel Selected Reservation")

        refresh_button = QPushButton("Refresh Reservations")

        modify_button.clicked.connect(self.modify_reservation)

        cancel_button.clicked.connect(self.cancel_reservation)

        refresh_button.clicked.connect(self.load_reservations)

        buttons = QHBoxLayout()
        buttons.addWidget(modify_button)
        buttons.addWidget(cancel_button)
        buttons.addWidget(refresh_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("All Student Reservations"))
        layout.addWidget(self.reservation_table)
        layout.addLayout(buttons)

        tab.setLayout(layout)

    def setup_user_tab(self, tab):
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(6)

        self.user_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Username",
                "Role",
                "Weekly Minutes",
                "Used Minutes",
                "Remaining"
            ]
        )

        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.user_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        role_button = QPushButton("Change Selected User Role")

        self.extra_minutes = QSpinBox()
        self.extra_minutes.setRange(15, 300)
        self.extra_minutes.setValue(60)
        self.extra_minutes.setSingleStep(15)
        self.extra_minutes.setSuffix(" minutes")

        time_button = QPushButton("Add Time to Student")

        refresh_button = QPushButton("Refresh Users")

        role_button.clicked.connect(self.change_selected_role)

        time_button.clicked.connect(self.add_time)

        refresh_button.clicked.connect(self.load_users)

        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Extra Time:"))
        time_layout.addWidget(self.extra_minutes)
        time_layout.addWidget(time_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(role_button)
        button_layout.addWidget(refresh_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("User Accounts and Lab Time"))
        layout.addWidget(self.user_table)
        layout.addLayout(time_layout)
        layout.addLayout(button_layout)

        tab.setLayout(layout)

    def load_users(self):
        users = get_all_users()

        self.user_table.setRowCount(len(users))

        for row, user in enumerate(users):
            weekly = user["weekly_minutes"]
            used = user["used_minutes"]

            remaining = max(0, weekly - used)

            values = [
                user["id"],
                user["username"],
                user["role"],
                weekly,
                used,
                remaining
            ]

            for column, value in enumerate(values):
                self.user_table.setItem(row, column, QTableWidgetItem(str(value)))

    def change_selected_role(self):
        row = self.user_table.currentRow()

        if row < 0:
            QMessageBox.warning(self, "No User Selected", "Select a user first.")
            return

        user_id = int(self.user_table.item(row, 0).text())

        username = self.user_table.item(row, 1).text()

        current_role = self.user_table.item(row, 2).text()

        answer = QMessageBox.question(
            self,
            "Change Role",
            (
                f"Change the role for "
                f"{username}?"
            )
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        success, message = change_user_role(self.user, user_id, current_role)

        if success:
            QMessageBox.information(self, "Role Updated", message)

            self.load_users()

        else:
            QMessageBox.warning(self, "Role Change Failed", message)

    def load_equipment(self):
        equipment = get_all_equipment()

        self.equipment_table.setRowCount(len(equipment))

        for row, item in enumerate(equipment):
            values = [
                item["id"],
                item["name"],
                item["status"]
            ]

            for column, value in enumerate(values):
                self.equipment_table.setItem(row, column, QTableWidgetItem(str(value)))

    def load_reservations(self):
        reservations = get_all_reservations()

        self.reservation_table.setRowCount(len(reservations))

        for row, reservation in enumerate(reservations):
            values = [
                reservation["id"],
                reservation["username"],
                reservation["equipment_name"],
                reservation["reservation_date"],
                reservation["start_time"],
                reservation["end_time"],
                reservation["status"]
            ]

            for column, value in enumerate(values):
                self.reservation_table.setItem(row, column, QTableWidgetItem(str(value)))

    def toggle_equipment(self):
        row = self.equipment_table.currentRow()

        if row < 0:
            QMessageBox.warning(self, "No Equipment Selected", "Select an equipment row first.")
            return

        equipment_id = int(self.equipment_table.item(row, 0).text())

        current_status = self.equipment_table.item(row, 2).text()

        success, message = change_equipment_status(self.user, equipment_id, current_status)

        if success:
            QMessageBox.information(self, "Equipment Updated", message)

            self.load_equipment()
        else:
            QMessageBox.warning(self, "Update Failed", message)

    def cancel_reservation(self):
        row = self.reservation_table.currentRow()

        if row < 0:
            QMessageBox.warning(self, "No Reservation Selected", "Select a reservation first.")
            return

        reservation_id = int(self.reservation_table.item(row, 0).text())

        answer = QMessageBox.question(self, "Cancel Reservation", "Cancel the selected reservation?")

        if answer != QMessageBox.StandardButton.Yes:
            return

        success, message = cancel_admin_reservation(self.user, reservation_id)

        if success:
            QMessageBox.information(self, "Reservation Cancelled", message)

            self.load_reservations()
        else:
            QMessageBox.warning(self, "Cancellation Failed", message)

    def add_time(self):
        row = self.user_table.currentRow()

        if row < 0:
            QMessageBox.warning(self, "No User Selected", "Select a student first.")
            return

        user_id = int(self.user_table.item(row, 0).text())

        role = self.user_table.item(row, 2).text()

        if role != "Student":
            QMessageBox.warning(self, "Invalid User", "Lab time can only be added to students.")
            return

        minutes = self.extra_minutes.value()

        success, message = add_student_time(self.user, user_id, minutes)

        if success:
            QMessageBox.information(self, "Time Added", message)

            self.load_users()

        else:
            QMessageBox.warning(self, "Update Failed", message)

    def modify_reservation(self):
        row = self.reservation_table.currentRow()

        if row < 0:
            QMessageBox.warning(self, "No Reservation Selected", "Select a reservation first.")
            return

        reservation_id = int(self.reservation_table.item(row, 0).text())

        reservation = get_reservation_for_admin(reservation_id)

        if not reservation:
            QMessageBox.warning(self, "Error", "Reservation was not found.")
            return

        dialog = AdminReservationDialog(reservation, self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        equipment_id = dialog.equipment_combo.currentData()

        reservation_date = dialog.date_input.date().toString("yyyy-MM-dd")

        start_time, end_time = dialog.time_combo.currentData()

        success, message = modify_admin_reservation(
            self.user,
            reservation_id,
            equipment_id,
            reservation_date,
            start_time,
            end_time
        )

        if success:
            QMessageBox.information(self, "Reservation Updated", message)

            self.load_reservations()

        else:
            QMessageBox.warning(self, "Modification Failed", message)