from datetime import datetime, timedelta

from app.database import (
    add_reservation,
    start_lab_session
)


def create_debug_session(user, equipment_id, equipment_name, duration_minutes):
    if user["role"] != "Student":
        return False, "Only student accounts can launch test sessions."

    if equipment_id is None:
        return False, "Select laboratory equipment."

    if duration_minutes < 1:
        return False, "The session duration must be at least one minute."

    current_time = datetime.now().replace(second=0, microsecond=0)

    end_time = current_time + timedelta(minutes=duration_minutes)

    if end_time.date() != current_time.date():
        return False, "A debug session cannot continue past midnight."

    reservation_date = current_time.strftime("%Y-%m-%d")

    start_time = current_time.strftime("%H:%M")

    reservation_end_time = end_time.strftime("%H:%M")

    try:
        reservation_id = add_reservation(
            user["id"],
            equipment_id,
            reservation_date,
            start_time,
            reservation_end_time
        )

        started_at = datetime.now().isoformat(timespec="seconds")

        session_id = start_lab_session(reservation_id, user["id"], started_at)

    except Exception as error:
        return False, f"Unable to create debug session: {error}"

    session = {
        "session_id": session_id,
        "reservation_id": reservation_id,
        "equipment_name": equipment_name,
        "reservation_date": reservation_date,
        "start_time": start_time,
        "end_time": reservation_end_time,
        "debug_mode": True
    }

    return True, session