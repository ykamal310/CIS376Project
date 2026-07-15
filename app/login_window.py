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


class CreateAccountDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Create Account")
        self.setFixedSize(350, 220)

        self.username = QLineEdit()

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

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

        self.setWindowTitle("Remote Lab Platform")
        self.setFixedSize(350, 250)

        self.title = QLabel("Remote Laboratory Platform")

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Log In")
        self.create_button = QPushButton("Create Account")
        self.logout_button = QPushButton("Log Out")
        self.logout_button.hide()

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_button)
        layout.addWidget(self.create_button)
        layout.addWidget(self.logout_button)

        self.setLayout(layout)

        self.login_button.clicked.connect(self.log_in)
        self.create_button.clicked.connect(self.open_create_account)
        self.logout_button.clicked.connect(self.log_out)
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

        self.title.setText(
            f"Logged in as {user['username']} ({user['role']})"
        )

        self.username.hide()
        self.password.hide()
        self.login_button.hide()
        self.create_button.hide()
        self.logout_button.show()

    def open_create_account(self):
        dialog = CreateAccountDialog()

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.username.setText(dialog.username.text())
            self.password.clear()

    def log_out(self):
        self.username.clear()
        self.password.clear()
        self.title.setText("Remote Laboratory Platform")

        self.username.show()
        self.password.show()
        self.login_button.show()
        self.create_button.show()
        self.logout_button.hide()