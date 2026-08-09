import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox
)

from app.authentication import create_account

from app.database import (
    create_tables,
    get_user
)

from app.experiment_manager import (
    sync_experiment_catalog
)

from app.login_window import LoginWindow


app = QApplication(sys.argv)

try:
    create_tables()

    sync_experiment_catalog()

except Exception as error:
    QMessageBox.critical(
        None,
        "Startup Error",
        (
            "The application could not start.\n\n"
            f"{error}"
        )
    )

    sys.exit(1)


if not get_user("admin"):
    create_account(
        "admin",
        "Admin123",
        "Administrator"
    )


window = LoginWindow()

window.show()

sys.exit(
    app.exec()
)