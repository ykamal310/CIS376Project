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
            result TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (experiment_id) REFERENCES experiments(id)
        );

        CREATE TABLE IF NOT EXISTS time_budgets (
            user_id INTEGER PRIMARY KEY,
            weekly_minutes INTEGER DEFAULT 300,
            used_minutes INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )

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