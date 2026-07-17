from PyQt6.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox
)

from app.authentication import create_account, login
from app.dashboard_window import DashboardWindow


class CreateAccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Create Account")
        self.setFixedSize(350, 220)

        self.username = QLineEdit()

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.create_button = QPushButton("Create Account")
        self.cancel_button = QPushButton("Cancel")

        form = QFormLayout()
        form.addRow("Create Username:", self.username)
        form.addRow("Create Password:", self.password)
        form.addRow("Retype Password:", self.confirm_password)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.create_button)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

        self.create_button.clicked.connect(self.create_user)
        self.cancel_button.clicked.connect(self.reject)

    def create_user(self):
        username = self.username.text()
        password = self.password.text()
        confirmation = self.confirm_password.text()

        if password != confirmation:
            QMessageBox.warning(
                self,
                "Error",
                "Passwords do not match."
            )
            return

        success, message = create_account(username, password)

        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", message)


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.dashboard = None

        self.setWindowTitle("Remote Lab Platform")
        self.setFixedSize(350, 250)

        title = QLabel("Remote Laboratory Platform")

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        login_button = QPushButton("Log In")
        create_button = QPushButton("Create Account")

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(login_button)
        layout.addWidget(create_button)

        self.setLayout(layout)

        login_button.clicked.connect(self.log_in)
        create_button.clicked.connect(self.open_create_account)
        self.password.returnPressed.connect(self.log_in)

    def log_in(self):
        user = login(
            self.username.text(),
            self.password.text()
        )

        if not user:
            QMessageBox.warning(
                self,
                "Login Failed",
                "Incorrect username or password."
            )
            return

        self.dashboard = DashboardWindow(user)
        self.dashboard.logged_out.connect(self.return_to_login)
        self.dashboard.show()

        self.hide()

    def open_create_account(self):
        dialog = CreateAccountDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.username.setText(dialog.username.text())
            self.password.clear()

    def return_to_login(self):
        self.password.clear()
        self.show()