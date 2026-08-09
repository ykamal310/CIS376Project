import sqlite3
import sys

from datetime import date, timedelta
from pathlib import Path


if getattr(sys, "frozen", False):
    BASE_FOLDER = Path(sys.executable).parent
else:
    BASE_FOLDER = Path(__file__).resolve().parent.parent


DATABASE = BASE_FOLDER / "data" / "remote_lab.db"


def get_connection():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE, timeout=5)

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    connection.execute("PRAGMA busy_timeout = 5000")

    connection.execute("PRAGMA journal_mode = WAL")

    return connection


def get_current_week_start():
    today = date.today()

    monday = today - timedelta(days=today.weekday())

    return monday.isoformat()


def create_tables():
    connection = get_connection()

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'Available',
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            equipment_id INTEGER NOT NULL,
            reservation_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            status TEXT DEFAULT 'Scheduled',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        );

        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS experiment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            experiment_id INTEGER NOT NULL,
            reservation_id INTEGER,
            result TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (experiment_id) REFERENCES experiments(id),
            FOREIGN KEY (reservation_id) REFERENCES reservations(id)
        );

        CREATE TABLE IF NOT EXISTS time_budgets (
            user_id INTEGER PRIMARY KEY,
            weekly_minutes INTEGER DEFAULT 300,
            used_minutes INTEGER DEFAULT 0,
            week_start TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS lab_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY (reservation_id)
                REFERENCES reservations(id),
            FOREIGN KEY (user_id)
                REFERENCES users(id)
        );
        """
    )

    equipment_columns = {
        column["name"]
        for column in connection.execute(
            "PRAGMA table_info(equipment)"
        ).fetchall()
    }

    if "active" not in equipment_columns:
        connection.execute(
            """
            ALTER TABLE equipment
            ADD COLUMN active INTEGER DEFAULT 1
            """
        )

    result_columns = {
        column["name"]
        for column in connection.execute(
            "PRAGMA table_info(experiment_results)"
        ).fetchall()
    }

    if "reservation_id" not in result_columns:
        connection.execute(
            """
            ALTER TABLE experiment_results
            ADD COLUMN reservation_id INTEGER
            """
        )

    if "created_at" not in result_columns:
        connection.execute(
            """
            ALTER TABLE experiment_results
            ADD COLUMN created_at TEXT
            """
        )

    budget_columns = {
        column["name"]
        for column in connection.execute(
            "PRAGMA table_info(time_budgets)"
        ).fetchall()
    }

    if "week_start" not in budget_columns:
        connection.execute(
            """
            ALTER TABLE time_budgets
            ADD COLUMN week_start TEXT
            """
        )

    connection.execute(
        """
        UPDATE time_budgets
        SET week_start = ?
        WHERE week_start IS NULL
        """,
        (get_current_week_start(),)
    )

    connection.commit()
    connection.close()


def add_user(username, password, role):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
            """,
            (username, password, role)
        )

        if role == "Student":
            connection.execute(
                """
                INSERT INTO time_budgets (
                    user_id,
                    week_start
                )
                VALUES (?, ?)
                """,
                (cursor.lastrowid, get_current_week_start())
            )

        connection.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        connection.close()


def get_user(username):
    connection = get_connection()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    connection.close()
    return user


def get_available_equipment():
    connection = get_connection()

    equipment = connection.execute(
        """
        SELECT *
        FROM equipment
        WHERE status = 'Available'
        AND active = 1
        ORDER BY name
        """
    ).fetchall()

    connection.close()

    return equipment


def reservation_conflicts(equipment_id, reservation_date, start_time, end_time):
    connection = get_connection()

    conflict = connection.execute(
        """
        SELECT id
        FROM reservations
        WHERE equipment_id = ?
        AND reservation_date = ?
        AND status = 'Scheduled'
        AND start_time < ?
        AND end_time > ?
        """,
        (
            equipment_id,
            reservation_date,
            end_time,
            start_time
        )
    ).fetchone()

    connection.close()

    return conflict is not None


def add_reservation(
    user_id,
    equipment_id,
    reservation_date,
    start_time,
    end_time
):
    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")

        conflict = connection.execute(
            """
            SELECT id
            FROM reservations
            WHERE equipment_id = ?
            AND reservation_date = ?
            AND status = 'Scheduled'
            AND start_time < ?
            AND end_time > ?
            """,
            (
                equipment_id,
                reservation_date,
                end_time,
                start_time
            )
        ).fetchone()

        if conflict:
            connection.rollback()
            return None

        cursor = connection.execute(
            """
            INSERT INTO reservations (
                user_id,
                equipment_id,
                reservation_date,
                start_time,
                end_time
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                equipment_id,
                reservation_date,
                start_time,
                end_time
            )
        )

        connection.commit()

        return cursor.lastrowid

    except sqlite3.Error:
        connection.rollback()
        return None

    finally:
        connection.close()


def get_user_reservations(user_id):
    connection = get_connection()

    reservations = connection.execute(
        """
        SELECT
            reservations.id,
            reservations.reservation_date,
            reservations.start_time,
            reservations.end_time,
            reservations.status,
            equipment.name AS equipment_name
        FROM reservations
        JOIN equipment
        ON reservations.equipment_id = equipment.id
        WHERE reservations.user_id = ?
        ORDER BY reservation_date, start_time
        """,
        (user_id,)
    ).fetchall()

    connection.close()
    return reservations


def get_reservation(reservation_id, user_id):
    connection = get_connection()

    reservation = connection.execute(
        """
        SELECT *
        FROM reservations
        WHERE id = ?
        AND user_id = ?
        """,
        (reservation_id, user_id)
    ).fetchone()

    connection.close()
    return reservation


def cancel_reservation(reservation_id, user_id):
    connection = get_connection()

    cursor = connection.execute(
        """
        UPDATE reservations
        SET status = 'Cancelled'
        WHERE id = ?
        AND user_id = ?
        AND status = 'Scheduled'
        """,
        (reservation_id, user_id)
    )

    connection.commit()

    cancelled = cursor.rowcount > 0

    connection.close()
    return cancelled


def get_time_budget(user_id):
    connection = get_connection()

    budget = connection.execute(
        """
        SELECT *
        FROM time_budgets
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    if not budget:
        connection.close()
        return None

    current_week = get_current_week_start()

    if budget["week_start"] != current_week:
        connection.execute(
            """
            UPDATE time_budgets
            SET used_minutes = 0,
                week_start = ?
            WHERE user_id = ?
            """,
            (current_week, user_id)
        )

        connection.commit()

        budget = connection.execute(
            """
            SELECT *
            FROM time_budgets
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

    connection.close()

    return budget


def update_used_minutes(user_id, minutes):
    get_time_budget(user_id)

    connection = get_connection()

    connection.execute(
        """
        UPDATE time_budgets
        SET used_minutes = MAX(
            0,
            used_minutes + ?
        )
        WHERE user_id = ?
        """,
        (minutes, user_id)
    )

    connection.commit()
    connection.close()


def start_lab_session(reservation_id, user_id, started_at):
    connection = get_connection()

    existing_session = connection.execute(
        """
        SELECT id
        FROM lab_sessions
        WHERE reservation_id = ?
        AND user_id = ?
        AND status = 'Active'
        """,
        (reservation_id, user_id)
    ).fetchone()

    if existing_session:
        connection.close()

        return existing_session["id"]

    cursor = connection.execute(
        """
        INSERT INTO lab_sessions (
            reservation_id,
            user_id,
            started_at
        )
        VALUES (?, ?, ?)
        """,
        (reservation_id, user_id, started_at)
    )

    connection.commit()

    session_id = cursor.lastrowid

    connection.close()

    return session_id


def end_lab_session(session_id, ended_at):
    connection = get_connection()

    cursor = connection.execute(
        """
        UPDATE lab_sessions
        SET ended_at = ?,
            status = 'Completed'
        WHERE id = ?
        AND status = 'Active'
        """,
        (ended_at, session_id)
    )

    connection.commit()

    updated = cursor.rowcount > 0

    connection.close()

    return updated


def complete_reservation(reservation_id):
    connection = get_connection()

    connection.execute(
        """
        UPDATE reservations
        SET status = 'Completed'
        WHERE id = ?
        AND status = 'Scheduled'
        """,
        (reservation_id,)
    )

    connection.commit()
    connection.close()


def get_experiments():
    connection = get_connection()

    experiments = connection.execute(
        """
        SELECT *
        FROM experiments
        ORDER BY name
        """
    ).fetchall()

    connection.close()

    return experiments


def save_experiment_result(
    user_id,
    experiment_id,
    reservation_id,
    result,
    created_at
):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO experiment_results (
            user_id,
            experiment_id,
            reservation_id,
            result,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            experiment_id,
            reservation_id,
            result,
            created_at
        )
    )

    connection.commit()

    result_id = cursor.lastrowid

    connection.close()

    return result_id


def get_user_reservation_history(user_id):
    connection = get_connection()

    reservations = connection.execute(
        """
        SELECT
            reservations.id,
            reservations.reservation_date,
            reservations.start_time,
            reservations.end_time,
            reservations.status,
            equipment.name AS equipment_name
        FROM reservations
        JOIN equipment
        ON reservations.equipment_id = equipment.id
        WHERE reservations.user_id = ?
        AND (
            reservations.status != 'Scheduled'
            OR datetime(
                reservations.reservation_date
                || ' '
                || reservations.end_time
            ) < datetime('now', 'localtime')
        )
        ORDER BY
            reservations.reservation_date DESC,
            reservations.start_time DESC
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    return reservations


def get_user_experiment_results(user_id):
    connection = get_connection()

    results = connection.execute(
        """
        SELECT
            experiment_results.id,
            experiment_results.reservation_id,
            experiment_results.result,
            experiment_results.created_at,
            experiments.name AS experiment_name
        FROM experiment_results
        JOIN experiments
        ON experiment_results.experiment_id = experiments.id
        WHERE experiment_results.user_id = ?
        ORDER BY
            experiment_results.created_at DESC,
            experiment_results.id DESC
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    return results


def get_all_equipment():
    connection = get_connection()

    equipment = connection.execute(
        """
        SELECT id, name, status
        FROM equipment
        WHERE active = 1
        ORDER BY name
        """
    ).fetchall()

    connection.close()

    return equipment

def update_equipment_status(equipment_id, new_status):
    connection = get_connection()

    cursor = connection.execute(
        """
        UPDATE equipment
        SET status = ?
        WHERE id = ?
        """,
        (new_status, equipment_id)
    )

    connection.commit()

    changed = cursor.rowcount > 0

    connection.close()

    return changed


def get_all_reservations():
    connection = get_connection()

    reservations = connection.execute(
        """
        SELECT
            reservations.id,
            reservations.user_id,
            users.username,
            equipment.name AS equipment_name,
            reservations.reservation_date,
            reservations.start_time,
            reservations.end_time,
            reservations.status
        FROM reservations
        JOIN users
        ON reservations.user_id = users.id
        JOIN equipment
        ON reservations.equipment_id = equipment.id
        ORDER BY
            reservations.reservation_date DESC,
            reservations.start_time DESC
        """
    ).fetchall()

    connection.close()

    return reservations


def get_reservation_for_admin(reservation_id):
    connection = get_connection()

    reservation = connection.execute(
        """
        SELECT
            id,
            user_id,
            equipment_id,
            reservation_date,
            start_time,
            end_time,
            status
        FROM reservations
        WHERE id = ?
        """,
        (reservation_id,)
    ).fetchone()

    connection.close()

    return reservation


def mark_reservation_cancelled(reservation_id):
    connection = get_connection()

    cursor = connection.execute(
        """
        UPDATE reservations
        SET status = 'Cancelled'
        WHERE id = ?
        AND status = 'Scheduled'
        """,
        (reservation_id,)
    )

    connection.commit()

    changed = cursor.rowcount > 0

    connection.close()

    return changed


def get_all_users():
    connection = get_connection()

    current_week = get_current_week_start()

    connection.execute(
        """
        UPDATE time_budgets
        SET used_minutes = 0,
            week_start = ?
        WHERE week_start IS NULL
        OR week_start != ?
        """,
        (current_week, current_week)
    )

    connection.commit()

    users = connection.execute(
        """
        SELECT
            users.id,
            users.username,
            users.role,
            COALESCE(
                time_budgets.weekly_minutes,
                0
            ) AS weekly_minutes,
            COALESCE(
                time_budgets.used_minutes,
                0
            ) AS used_minutes
        FROM users
        LEFT JOIN time_budgets
        ON users.id = time_budgets.user_id
        ORDER BY users.username
        """
    ).fetchall()

    connection.close()

    return users


def update_user_role(user_id, new_role):
    connection = get_connection()

    cursor = connection.execute(
        """
        UPDATE users
        SET role = ?
        WHERE id = ?
        """,
        (new_role, user_id)
    )

    if new_role == "Student":
        connection.execute(
            """
            INSERT OR IGNORE INTO time_budgets (
                user_id,
                weekly_minutes,
                used_minutes,
                week_start
            )
            VALUES (?, 300, 0, ?)
            """,
            (user_id, get_current_week_start())
        )

    connection.commit()

    changed = cursor.rowcount > 0

    connection.close()

    return changed


def extend_time_budget(user_id, extra_minutes):
    connection = get_connection()

    cursor = connection.execute(
        """
        UPDATE time_budgets
        SET weekly_minutes =
            weekly_minutes + ?
        WHERE user_id = ?
        """,
        (extra_minutes, user_id)
    )

    connection.commit()

    changed = cursor.rowcount > 0

    connection.close()

    return changed


def reservation_conflicts_except(
    reservation_id,
    equipment_id,
    reservation_date,
    start_time,
    end_time
):
    connection = get_connection()

    conflict = connection.execute(
        """
        SELECT id
        FROM reservations
        WHERE equipment_id = ?
        AND reservation_date = ?
        AND status = 'Scheduled'
        AND id != ?
        AND start_time < ?
        AND end_time > ?
        """,
        (
            equipment_id,
            reservation_date,
            reservation_id,
            end_time,
            start_time
        )
    ).fetchone()

    connection.close()

    return conflict is not None


def update_reservation(
    reservation_id,
    equipment_id,
    reservation_date,
    start_time,
    end_time
):
    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")

        conflict = connection.execute(
            """
            SELECT id
            FROM reservations
            WHERE equipment_id = ?
            AND reservation_date = ?
            AND status = 'Scheduled'
            AND id != ?
            AND start_time < ?
            AND end_time > ?
            """,
            (
                equipment_id,
                reservation_date,
                reservation_id,
                end_time,
                start_time
            )
        ).fetchone()

        if conflict:
            connection.rollback()
            return False

        cursor = connection.execute(
            """
            UPDATE reservations
            SET equipment_id = ?,
                reservation_date = ?,
                start_time = ?,
                end_time = ?
            WHERE id = ?
            AND status = 'Scheduled'
            """,
            (
                equipment_id,
                reservation_date,
                start_time,
                end_time,
                reservation_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except sqlite3.Error:
        connection.rollback()
        return False

    finally:
        connection.close()


def get_next_reservation(user_id):
    connection = get_connection()

    reservation = connection.execute(
        """
        SELECT
            reservations.id,
            reservations.reservation_date,
            reservations.start_time,
            reservations.end_time,
            equipment.name AS equipment_name
        FROM reservations
        JOIN equipment
        ON reservations.equipment_id = equipment.id
        WHERE reservations.user_id = ?
        AND reservations.status = 'Scheduled'
        AND datetime(
            reservations.reservation_date
            || ' '
            || reservations.end_time
        ) >= datetime('now', 'localtime')
        ORDER BY
            reservations.reservation_date,
            reservations.start_time
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    connection.close()

    return reservation

def get_or_create_experiment(name, description):
    connection = get_connection()

    experiment = connection.execute(
        """
        SELECT *
        FROM experiments
        WHERE name = ?
        """,
        (name,)
    ).fetchone()

    if experiment:
        connection.close()
        return experiment["id"]

    cursor = connection.execute(
        """
        INSERT INTO experiments (
            name,
            description
        )
        VALUES (?, ?)
        """,
        (
            name,
            description
        )
    )

    connection.commit()

    experiment_id = cursor.lastrowid

    connection.close()

    return experiment_id

def sync_equipment_catalog(
    equipment_names
):
    unique_names = sorted(
        {
            name.strip()
            for name in equipment_names
            if name and name.strip()
        }
    )

    connection = get_connection()

    connection.execute(
        """
        UPDATE equipment
        SET active = 0
        """
    )

    for name in unique_names:
        equipment = connection.execute(
            """
            SELECT id
            FROM equipment
            WHERE name = ?
            ORDER BY id
            LIMIT 1
            """,
            (name,)
        ).fetchone()

        if equipment:
            connection.execute(
                """
                UPDATE equipment
                SET active = 1
                WHERE id = ?
                """,
                (equipment["id"],)
            )

        else:
            connection.execute(
                """
                INSERT INTO equipment (
                    name,
                    status,
                    active
                )
                VALUES (?, 'Available', 1)
                """,
                (name,)
            )

    connection.commit()
    connection.close()