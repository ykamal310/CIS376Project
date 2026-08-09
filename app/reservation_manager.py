from datetime import date, datetime

from app.database import (
    add_reservation,
    cancel_reservation,
    get_reservation,
    get_time_budget,
    reservation_conflicts,
    reservation_conflicts_except,
    update_reservation,
    update_used_minutes
)


TIME_SLOTS = [
    ("09:00", "10:00"),
    ("10:00", "11:00"),
    ("11:00", "12:00"),
    ("12:00", "13:00"),
    ("13:00", "14:00"),
    ("14:00", "15:00"),
    ("15:00", "16:00"),
    ("16:00", "17:00")
]


def get_duration_minutes(start_time, end_time):
    start_value = datetime.strptime(
        start_time,
        "%H:%M"
    )

    end_value = datetime.strptime(
        end_time,
        "%H:%M"
    )

    duration = end_value - start_value

    return int(duration.total_seconds() / 60)


def get_remaining_minutes(user_id):
    budget = get_time_budget(user_id)

    if not budget:
        return 0

    return max(
        0,
        budget["weekly_minutes"] - budget["used_minutes"]
    )


def get_available_slots(equipment_id, reservation_date):
    try:
        selected_date = datetime.strptime(
            reservation_date,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return []

    if selected_date < date.today():
        return []

    available_slots = []

    for start_time, end_time in TIME_SLOTS:
        slot_start = datetime.combine(
            selected_date,
            datetime.strptime(
                start_time,
                "%H:%M"
            ).time()
        )

        if slot_start <= datetime.now():
            continue

        conflict = reservation_conflicts(
            equipment_id,
            reservation_date,
            start_time,
            end_time
        )

        if not conflict:
            available_slots.append(
                {
                    "start_time": start_time,
                    "end_time": end_time
                }
            )

    return available_slots


def create_reservation(
    user,
    equipment_id,
    reservation_date,
    start_time,
    end_time
):
    if user["role"] != "Student":
        return False, "Only students can create reservations."

    try:
        selected_date = datetime.strptime(
            reservation_date,
            "%Y-%m-%d"
        ).date()

        start_value = datetime.strptime(
            start_time,
            "%H:%M"
        ).time()

        end_value = datetime.strptime(
            end_time,
            "%H:%M"
        ).time()

    except ValueError:
        return False, "Invalid reservation date or time."

    start_date_time = datetime.combine(
        selected_date,
        start_value
    )

    end_date_time = datetime.combine(
        selected_date,
        end_value
    )

    if selected_date < date.today():
        return False, "Reservations cannot be created in the past."

    if start_date_time <= datetime.now():
        return False, "The selected reservation time has already passed."

    if end_date_time <= start_date_time:
        return False, "The end time must be after the start time."

    if reservation_conflicts(
        equipment_id,
        reservation_date,
        start_time,
        end_time
    ):
        return False, "This time slot is already reserved."

    duration = get_duration_minutes(
        start_time,
        end_time
    )

    remaining_minutes = get_remaining_minutes(
        user["id"]
    )

    if duration > remaining_minutes:
        return (
            False,
            "This reservation exceeds your remaining lab time."
        )

    add_reservation(
        user["id"],
        equipment_id,
        reservation_date,
        start_time,
        end_time
    )

    update_used_minutes(
        user["id"],
        duration
    )

    return True, "Reservation created successfully."


def cancel_user_reservation(user, reservation_id):
    reservation = get_reservation(
        reservation_id,
        user["id"]
    )

    if not reservation:
        return False, "Reservation could not be found."

    if reservation["status"] != "Scheduled":
        return False, "This reservation is not active."

    start_date_time = datetime.strptime(
        (
            f"{reservation['reservation_date']} "
            f"{reservation['start_time']}"
        ),
        "%Y-%m-%d %H:%M"
    )

    if start_date_time <= datetime.now():
        return False, "Only future reservations can be cancelled."

    duration = get_duration_minutes(
        reservation["start_time"],
        reservation["end_time"]
    )

    cancelled = cancel_reservation(
        reservation_id,
        user["id"]
    )

    if not cancelled:
        return False, "The reservation could not be cancelled."

    update_used_minutes(
        user["id"],
        -duration
    )

    return True, "Reservation cancelled successfully."
def modify_reservation(
    user,
    reservation_id,
    equipment_id,
    reservation_date,
    start_time,
    end_time
):
    reservation = get_reservation(
        reservation_id,
        user["id"]
    )

    if not reservation:
        return False, "Reservation was not found."

    if reservation["status"] != "Scheduled":
        return False, "Only scheduled reservations can be changed."

    try:
        new_date = datetime.strptime(
            reservation_date,
            "%Y-%m-%d"
        ).date()

        new_start = datetime.strptime(
            start_time,
            "%H:%M"
        ).time()

        new_end = datetime.strptime(
            end_time,
            "%H:%M"
        ).time()

    except ValueError:
        return False, "Invalid date or time."

    start_date_time = datetime.combine(
        new_date,
        new_start
    )

    end_date_time = datetime.combine(
        new_date,
        new_end
    )

    if start_date_time <= datetime.now():
        return False, "The new reservation must be in the future."

    if end_date_time <= start_date_time:
        return False, "End time must be after start time."

    conflict = reservation_conflicts_except(
        reservation_id,
        equipment_id,
        reservation_date,
        start_time,
        end_time
    )

    if conflict:
        return False, "That time slot is already reserved."

    old_minutes = get_duration_minutes(
        reservation["start_time"],
        reservation["end_time"]
    )

    new_minutes = get_duration_minutes(
        start_time,
        end_time
    )

    difference = new_minutes - old_minutes

    if difference > 0:
        remaining = get_remaining_minutes(
            user["id"]
        )

        if difference > remaining:
            return (
                False,
                "You do not have enough remaining lab time."
            )

    changed = update_reservation(
        reservation_id,
        equipment_id,
        reservation_date,
        start_time,
        end_time
    )

    if not changed:
        return False, "Reservation could not be changed."

    if difference != 0:
        update_used_minutes(
            user["id"],
            difference
        )

    return True, "Reservation updated successfully."