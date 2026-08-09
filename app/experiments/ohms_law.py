NAME = "Ohm's Law"

DESCRIPTION = (
    "Calculate electrical current using "
    "voltage and resistance."
)

EQUIPMENT = "Electronics Workbench"

FIELDS = (
    "Voltage (V):",
    "Resistance (Ohms):"
)


def run(first_value, second_value):
    try:
        voltage = float(first_value)
        resistance = float(second_value)

    except ValueError:
        return False, "Voltage and resistance must be numbers."

    if voltage <= 0:
        return False, "Voltage must be greater than zero."

    if resistance <= 0:
        return False, "Resistance must be greater than zero."

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
        "experiment_name": NAME,
        "summary": f"Calculated Current: {current:.3f} A",
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