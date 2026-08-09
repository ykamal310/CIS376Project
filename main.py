import sys

from PyQt6.QtWidgets import QApplication

from app.authentication import create_account
from app.database import create_tables
from app.login_window import LoginWindow


create_tables()

success, message = create_account(
    "adm",
    "adm",
    "Administrator"
)

print("Admin setup:", success, message)

app = QApplication(sys.argv)

window = LoginWindow()
window.show()

sys.exit(app.exec())