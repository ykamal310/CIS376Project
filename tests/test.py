import tempfile
import unittest

from datetime import date, timedelta
from pathlib import Path

import app.database as database

from app.authentication import (
    create_account,
    login
)

from app.experiment_manager import (
    run_experiment
)

from app.reservation_manager import (
    create_reservation
)


class RemoteLabTests(unittest.TestCase):

    def setUp(self):
        self.temp_folder = (
            tempfile.TemporaryDirectory()
        )

        database.DATABASE = (
            Path(self.temp_folder.name)
            / "test_lab.db"
        )

        database.create_tables()

        create_account(
            "student1",
            "Password123",
            "Student"
        )

        create_account(
            "student2",
            "Password123",
            "Student"
        )

        self.student1 = login(
            "student1",
            "Password123"
        )

        self.student2 = login(
            "student2",
            "Password123"
        )

    def tearDown(self):
        self.temp_folder.cleanup()

    def test_valid_login(self):
        user = login(
            "student1",
            "Password123"
        )

        self.assertIsNotNone(
            user
        )

    def test_wrong_password(self):
        user = login(
            "student1",
            "wrongpassword"
        )

        self.assertIsNone(
            user
        )

    def test_reservation_conflict(self):
        equipment = (
            database.get_available_equipment()
        )

        tomorrow = (
            date.today()
            + timedelta(days=1)
        ).isoformat()

        first, message = create_reservation(
            self.student1,
            equipment[0]["id"],
            tomorrow,
            "09:00",
            "10:00"
        )

        second, message = create_reservation(
            self.student2,
            equipment[0]["id"],
            tomorrow,
            "09:00",
            "10:00"
        )

        self.assertTrue(
            first
        )

        self.assertFalse(
            second
        )

    def test_time_budget_limit(self):
        connection = (
            database.get_connection()
        )

        connection.execute(
            """
            UPDATE time_budgets
            SET weekly_minutes = 30
            WHERE user_id = ?
            """,
            (
                self.student1["id"],
            )
        )

        connection.commit()
        connection.close()

        equipment = (
            database.get_available_equipment()
        )

        tomorrow = (
            date.today()
            + timedelta(days=1)
        ).isoformat()

        success, message = create_reservation(
            self.student1,
            equipment[0]["id"],
            tomorrow,
            "10:00",
            "11:00"
        )

        self.assertFalse(
            success
        )

    def test_weekly_budget_reset(self):
        old_week = (
            date.today()
            - timedelta(days=8)
        ).isoformat()

        connection = (
            database.get_connection()
        )

        connection.execute(
            """
            UPDATE time_budgets
            SET used_minutes = 180,
                week_start = ?
            WHERE user_id = ?
            """,
            (
                old_week,
                self.student1["id"]
            )
        )

        connection.commit()
        connection.close()

        budget = database.get_time_budget(
            self.student1["id"]
        )

        self.assertEqual(
            budget["used_minutes"],
            0
        )

    def test_ohms_law(self):
        success, result = run_experiment(
            "Ohm's Law",
            "12",
            "6"
        )

        self.assertTrue(
            success
        )

        self.assertEqual(
            result["record"]["current_a"],
            2
        )


if __name__ == "__main__":
    unittest.main()