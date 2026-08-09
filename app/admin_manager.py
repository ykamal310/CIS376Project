from datetime import datetime

from app.database import (
    get_reservation_for_admin,
    mark_reservation_cancelled,
    update_equipment_status,
    update_used_minutes
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