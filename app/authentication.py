from werkzeug.security import generate_password_hash, check_password_hash

from app.database import add_user, get_user


def create_account(username, password, role="Student"):
    username = username.strip()

    if not username or not password:
        return False, "Enter a username and password."

    password_hash = generate_password_hash(password)

    if not add_user(username, password_hash, role):
        return False, "Username already exists."

    return True, "Account created successfully."


def login(username, password):
    user = get_user(username.strip())

    if user and check_password_hash(user["password"], password):
        return user

    return None