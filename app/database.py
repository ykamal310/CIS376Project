import sqlite3
from pathlib import Path


DATABASE = Path("data/remote_lab.db")


def get_connection():
    DATABASE.parent.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


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
            status TEXT DEFAULT 'Available'
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

    equipment_count = connection.execute(
        "SELECT COUNT(*) FROM equipment"
    ).fetchone()[0]

    if equipment_count == 0:
        connection.executemany(
            """
            INSERT INTO equipment (name)
            VALUES (?)
            """,
            [
                ("Chemistry Workstation",),
                ("Electronics Workbench",),
                ("Physics Simulation Station",)
            ]
        )

    experiment_count = connection.execute(
        "SELECT COUNT(*) FROM experiments"
    ).fetchone()[0]

    if experiment_count == 0:
        connection.executemany(
            """
            INSERT INTO experiments (
                name,
                description
            )
            VALUES (?, ?)
            """,
            [
                (
                    "Ohm's Law",
                    (
                        "Calculate electrical current using "
                        "voltage and resistance."
                    )
                ),
                (
                    "Pendulum Period",
                    (
                        "Calculate the period of a pendulum "
                        "using length and gravitational acceleration."
                    )
                )
            ]
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
                INSERT INTO time_budgets (user_id)
                VALUES (?)
                """,
                (cursor.lastrowid,)
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
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    connection.close()
    return user


def get_available_equipment():
    connection = get_connection()

    equipment = connection.execute(
        """
        SELECT * FROM equipment
        WHERE status = 'Available'
        ORDER BY name
        """
    ).fetchall()

    connection.close()
    return equipment


def reservation_conflicts(
    equipment_id,
    reservation_date,
    start_time,
    end_time
):
    connection = get_connection()

    conflict = connection.execute(
        """
        SELECT id FROM reservations
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
    reservation_id = cursor.lastrowid
    connection.close()

    return reservation_id


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
        SELECT * FROM reservations
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
        SELECT * FROM time_budgets
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    connection.close()
    return budget


def update_used_minutes(user_id, minutes):
    connection = get_connection()

    connection.execute(
        """
        UPDATE time_budgets
        SET used_minutes = MAX(0, used_minutes + ?)
        WHERE user_id = ?
        """,
        (minutes, user_id)
    )

    connection.commit()
    connection.close()

def start_lab_session(
    reservation_id,
    user_id,
    started_at
):
    connection = get_connection()

    existing_session = connection.execute(
        """
        SELECT id FROM lab_sessions
        WHERE reservation_id = ?
        AND user_id = ?
        AND status = 'Active'
        """,
        (
            reservation_id,
            user_id
        )
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
        (
            reservation_id,
            user_id,
            started_at
        )
    )

    connection.commit()
    session_id = cursor.lastrowid
    connection.close()

    return session_id


def end_lab_session(
    session_id,
    ended_at
):
    connection = get_connection()

    cursor = connection.execute(
        """
        UPDATE lab_sessions
        SET ended_at = ?,
            status = 'Completed'
        WHERE id = ?
        AND status = 'Active'
        """,
        (
            ended_at,
            session_id
        )
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