from datetime import datetime


from app.database import (
    get_reservation_for_admin,
    mark_reservation_cancelled,
    update_equipment_status,
    update_used_minutes,
    update_user_role,
    extend_time_budget
)


def is_admin(user):
    return (
        user
        and user["role"] == "Administrator"
    )


def change_equipment_status(
    user,
    equipment_id,
    current_status
):
    if not is_admin(user):
        return False, "Administrator access is required."

    if current_status == "Available":
        new_status = "Unavailable"
    else:
        new_status = "Available"

    changed = update_equipment_status(
        equipment_id,
        new_status
    )

    if not changed:
        return False, "Equipment could not be updated."

    return (
        True,
        f"Equipment is now {new_status}."
    )


def cancel_admin_reservation(
    user,
    reservation_id
):
    if not is_admin(user):
        return False, "Administrator access is required."

    reservation = get_reservation_for_admin(
        reservation_id
    )

    if not reservation:
        return False, "Reservation was not found."

    if reservation["status"] != "Scheduled":
        return (
            False,
            "Only scheduled reservations can be cancelled."
        )

    changed = mark_reservation_cancelled(
        reservation_id
    )

    if not changed:
        return False, "Reservation could not be cancelled."

    start = datetime.strptime(
        reservation["start_time"],
        "%H:%M"
    )

    end = datetime.strptime(
        reservation["end_time"],
        "%H:%M"
    )

    minutes = int(
        (end - start).total_seconds() / 60
    )

    update_used_minutes(
        reservation["user_id"],
        -minutes
    )

    return True, "Reservation cancelled successfully."

def change_user_role(
    admin,
    user_id,
    current_role
):
    if not is_admin(admin):
        return False, "Administrator access is required."

    # don't let the admin accidentally remove
    # their own admin permissions
    if user_id == admin["id"]:
        return False, "You cannot change your own role."

    if current_role == "Student":
        new_role = "Administrator"
    else:
        new_role = "Student"

    changed = update_user_role(
        user_id,
        new_role
    )

    if not changed:
        return False, "User role could not be changed."

    return (
        True,
        f"User role changed to {new_role}."
    )


def add_student_time(
    admin,
    user_id,
    minutes
):
    if not is_admin(admin):
        return False, "Administrator access is required."

    if minutes <= 0:
        return False, "Minutes must be greater than zero."

    changed = extend_time_budget(
        user_id,
        minutes
    )

    if not changed:
        return (
            False,
            "This user does not have a student time budget."
        )

    return (
        True,
        f"Added {minutes} minutes to the student's weekly budget."
    )