import math


NAME = "Pendulum Period"

DESCRIPTION = (
    "Calculate the period of a pendulum "
    "using length and gravitational acceleration."
)

EQUIPMENT = "Physics Simulation Station"

FIELDS = (
    "Pendulum Length (m):",
    "Gravity (m/s²):"
)


def run(first_value, second_value):
    try:
        length = float(first_value)
        gravity = float(second_value)

    except ValueError:
        return False, "Length and gravity must be numbers."

    if length <= 0:
        return False, "Pendulum length must be greater than zero."

    if gravity <= 0:
        return False, "Gravity must be greater than zero."

    period = 2 * math.pi * math.sqrt(length / gravity)

    time_values = [
        period * index / 40
        for index in range(81)
    ]

    angle_values = [
        10 * math.cos(
            2 * math.pi * time_value / period
        )
        for time_value in time_values
    ]

    result = {
        "experiment_name": NAME,
        "summary": f"Calculated Period: {period:.3f} seconds",
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