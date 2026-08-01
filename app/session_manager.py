from datetime import datetime

from app.database import (
    complete_reservation,
    end_lab_session,
    get_user_reservations,
    start_lab_session
)


def get_active_reservation(user_id):
    current_time = datetime.now()

    reservations = get_user_reservations(
        user_id
    )

    for reservation in reservations:
        if reservation["status"] != "Scheduled":
            continue

        reservation_start = datetime.strptime(
            (
                f"{reservation['reservation_date']} "
                f"{reservation['start_time']}"
            ),
            "%Y-%m-%d %H:%M"
        )

        reservation_end = datetime.strptime(
            (
                f"{reservation['reservation_date']} "
                f"{reservation['end_time']}"
            ),
            "%Y-%m-%d %H:%M"
        )

        if reservation_start <= current_time < reservation_end:
            return reservation

    return None


def begin_session(user):
    if user["role"] != "Student":
        return (
            False,
            "Only students can access laboratory sessions."
        )

    reservation = get_active_reservation(
        user["id"]
    )

    if not reservation:
        return (
            False,
            "You do not have an active reservation."
        )

    started_at = datetime.now().isoformat(
        timespec="seconds"
    )

    session_id = start_lab_session(
        reservation["id"],
        user["id"],
        started_at
    )

    session = {
        "session_id": session_id,
        "reservation_id": reservation["id"],
        "equipment_name": reservation["equipment_name"],
        "reservation_date": reservation["reservation_date"],
        "start_time": reservation["start_time"],
        "end_time": reservation["end_time"]
    }

    return True, session


def finish_session(
    session_id,
    reservation_id=None,
    reservation_expired=False
):
    ended_at = datetime.now().isoformat(
        timespec="seconds"
    )

    end_lab_session(
        session_id,
        ended_at
    )

    if reservation_expired and reservation_id:
        complete_reservation(
            reservation_id
        )