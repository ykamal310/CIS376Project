from datetime import datetime

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas
)
from matplotlib.figure import Figure

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QMessageBox
)

from app.database import get_experiments
from app.experiment_manager import (
    get_experiment_fields,
    run_experiment,
    store_experiment_result
)
from app.session_manager import finish_session


class ExperimentWindow(QWidget):
    def __init__(self, user, session):
        super().__init__()

        self.user = user
        self.session = session

        self.current_result = None
        self.session_finished = False

        self.setWindowTitle(
            "Active Laboratory Session"
        )
        self.setFixedSize(800, 700)

        title = QLabel(
            "Remote Laboratory Experiment"
        )

        student_label = QLabel(
            f"Student: {user['username']}"
        )

        equipment_label = QLabel(
            (
                "Equipment: "
                f"{session['equipment_name']}"
            )
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

        self.experiment_combo = QComboBox()

        self.first_input_label = QLabel()
        self.first_input = QLineEdit()

        self.second_input_label = QLabel()
        self.second_input = QLineEdit()

        self.run_button = QPushButton(
            "Run Experiment"
        )

        self.save_button = QPushButton(
            "Save Result"
        )

        self.save_button.setEnabled(False)

        self.result_label = QLabel(
            "Run an experiment to view the result."
        )

        self.figure = Figure(
            figsize=(6, 3)
        )

        self.canvas = FigureCanvas(
            self.figure
        )

        self.axes = self.figure.add_subplot(
            111
        )

        end_button = QPushButton(
            "End Session"
        )

        experiment_form = QFormLayout()
        experiment_form.addRow(
            "Experiment:",
            self.experiment_combo
        )
        experiment_form.addRow(
            self.first_input_label,
            self.first_input
        )
        experiment_form.addRow(
            self.second_input_label,
            self.second_input
        )

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(student_label)
        layout.addWidget(equipment_label)
        layout.addWidget(reservation_label)
        layout.addWidget(self.remaining_time_label)
        layout.addLayout(experiment_form)
        layout.addWidget(self.run_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.canvas)
        layout.addWidget(self.save_button)
        layout.addWidget(end_button)

        self.setLayout(layout)

        self.experiment_combo.currentIndexChanged.connect(
            self.update_experiment_inputs
        )

        self.run_button.clicked.connect(
            self.run_selected_experiment
        )

        self.save_button.clicked.connect(
            self.save_current_result
        )

        end_button.clicked.connect(
            self.end_session_early
        )

        self.load_experiments()

        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.update_remaining_time
        )

        self.timer.start(1000)

        self.update_remaining_time()

    def load_experiments(self):
        self.experiment_combo.clear()

        experiments = get_experiments()

        for experiment in experiments:
            self.experiment_combo.addItem(
                experiment["name"],
                experiment["id"]
            )

        has_experiments = (
            self.experiment_combo.count() > 0
        )

        self.run_button.setEnabled(
            has_experiments
        )

        if not has_experiments:
            self.result_label.setText(
                "No experiments are available."
            )

        self.update_experiment_inputs()

    def update_experiment_inputs(self):
        experiment_name = (
            self.experiment_combo.currentText()
        )

        first_label, second_label = (
            get_experiment_fields(
                experiment_name
            )
        )

        self.first_input_label.setText(
            first_label
        )

        self.second_input_label.setText(
            second_label
        )

        self.first_input.clear()
        self.second_input.clear()

        self.current_result = None

        self.save_button.setEnabled(False)

        self.result_label.setText(
            "Run an experiment to view the result."
        )

        self.axes.clear()
        self.canvas.draw()

    def run_selected_experiment(self):
        experiment_name = (
            self.experiment_combo.currentText()
        )

        success, result = run_experiment(
            experiment_name,
            self.first_input.text(),
            self.second_input.text()
        )

        if not success:
            QMessageBox.warning(
                self,
                "Experiment Error",
                result
            )
            return

        self.current_result = result

        self.result_label.setText(
            result["summary"]
        )

        self.axes.clear()

        self.axes.plot(
            result["x_values"],
            result["y_values"]
        )

        self.axes.set_title(
            result["chart_title"]
        )

        self.axes.set_xlabel(
            result["x_label"]
        )

        self.axes.set_ylabel(
            result["y_label"]
        )

        self.axes.grid(True)

        self.figure.tight_layout()
        self.canvas.draw()

        self.save_button.setEnabled(True)

    def save_current_result(self):
        if not self.current_result:
            QMessageBox.warning(
                self,
                "Save Error",
                "Run an experiment before saving."
            )
            return

        experiment_id = (
            self.experiment_combo.currentData()
        )

        success, message = store_experiment_result(
            self.user,
            self.session,
            experiment_id,
            self.current_result
        )

        if success:
            QMessageBox.information(
                self,
                "Result Saved",
                message
            )

            self.save_button.setEnabled(False)

        else:
            QMessageBox.warning(
                self,
                "Save Error",
                message
            )

    def get_reservation_end(self):
        return datetime.strptime(
            (
                f"{self.session['reservation_date']} "
                f"{self.session['end_time']}"
            ),
            "%Y-%m-%d %H:%M"
        )

    def update_remaining_time(self):
        reservation_end = (
            self.get_reservation_end()
        )

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