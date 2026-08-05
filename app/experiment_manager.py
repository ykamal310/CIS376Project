import json
import math

from datetime import datetime

from app.database import save_experiment_result


EXPERIMENT_FIELDS = {
    "Ohm's Law": (
        "Voltage (V):",
        "Resistance (Ohms):"
    ),
    "Pendulum Period": (
        "Pendulum Length (m):",
        "Gravity (m/s²):"
    )
}


def get_experiment_fields(experiment_name):
    return EXPERIMENT_FIELDS.get(
        experiment_name,
        (
            "First Value:",
            "Second Value:"
        )
    )


def parse_positive_number(value, field_name):
    try:
        number = float(value)

    except ValueError:
        return (
            False,
            f"{field_name} must be a number."
        )

    if number <= 0:
        return (
            False,
            f"{field_name} must be greater than zero."
        )

    return True, number


def run_experiment(
    experiment_name,
    first_value,
    second_value
):
    if experiment_name == "Ohm's Law":
        return run_ohms_law(
            first_value,
            second_value
        )

    if experiment_name == "Pendulum Period":
        return run_pendulum(
            first_value,
            second_value
        )

    return (
        False,
        "The selected experiment is not available."
    )


def run_ohms_law(
    voltage_value,
    resistance_value
):
    voltage_valid, voltage = parse_positive_number(
        voltage_value,
        "Voltage"
    )

    if not voltage_valid:
        return False, voltage

    resistance_valid, resistance = parse_positive_number(
        resistance_value,
        "Resistance"
    )

    if not resistance_valid:
        return False, resistance

    current = voltage / resistance

    voltage_values = [
        voltage * index / 20
        for index in range(21)
    ]

    current_values = [
        value / resistance
        for value in voltage_values
    ]

    result = {
        "experiment_name": "Ohm's Law",
        "summary": (
            f"Calculated Current: "
            f"{current:.3f} A"
        ),
        "record": {
            "voltage_v": voltage,
            "resistance_ohms": resistance,
            "current_a": current
        },
        "x_values": voltage_values,
        "y_values": current_values,
        "x_label": "Voltage (V)",
        "y_label": "Current (A)",
        "chart_title": "Ohm's Law Simulation"
    }

    return True, result


def run_pendulum(
    length_value,
    gravity_value
):
    length_valid, length = parse_positive_number(
        length_value,
        "Pendulum length"
    )

    if not length_valid:
        return False, length

    gravity_valid, gravity = parse_positive_number(
        gravity_value,
        "Gravity"
    )

    if not gravity_valid:
        return False, gravity

    period = (
        2
        * math.pi
        * math.sqrt(length / gravity)
    )

    time_values = [
        period * index / 40
        for index in range(81)
    ]

    angle_values = [
        10
        * math.cos(
            2
            * math.pi
            * time_value
            / period
        )
        for time_value in time_values
    ]

    result = {
        "experiment_name": "Pendulum Period",
        "summary": (
            f"Calculated Period: "
            f"{period:.3f} seconds"
        ),
        "record": {
            "length_m": length,
            "gravity_m_per_s2": gravity,
            "period_seconds": period
        },
        "x_values": time_values,
        "y_values": angle_values,
        "x_label": "Time (seconds)",
        "y_label": "Angle (degrees)",
        "chart_title": "Pendulum Motion Simulation"
    }

    return True, result


def store_experiment_result(
    user,
    session,
    experiment_id,
    result
):
    created_at = datetime.now().isoformat(
        timespec="seconds"
    )

    stored_result = {
        "experiment": result["experiment_name"],
        "summary": result["summary"],
        "values": result["record"]
    }

    result_id = save_experiment_result(
        user["id"],
        experiment_id,
        session["reservation_id"],
        json.dumps(stored_result),
        created_at
    )

    return (
        True,
        (
            "Experiment result saved successfully. "
            f"Result ID: {result_id}"
        )
    )