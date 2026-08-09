NAME = "Solution Dilution"

DESCRIPTION = (
    "Calculate the final concentration of "
    "a diluted chemical solution."
)

EQUIPMENT = "Chemistry Workstation"

FIELDS = (
    "Initial Concentration (M):",
    "Dilution Factor:"
)


def run(first_value, second_value):
    try:
        concentration = float(first_value)
        dilution_factor = float(second_value)

    except ValueError:
        return False, "Concentration and dilution factor must be numbers."

    if concentration <= 0:
        return False, "Initial concentration must be greater than zero."

    if dilution_factor <= 0:
        return False, "Dilution factor must be greater than zero."

    final_concentration = (
        concentration / dilution_factor
    )

    factor_values = [
        1 + index
        for index in range(20)
    ]

    concentration_values = [
        concentration / factor
        for factor in factor_values
    ]

    result = {
        "experiment_name": NAME,
        "summary": (
            "Final Concentration: "
            f"{final_concentration:.3f} M"
        ),
        "record": {
            "initial_concentration_m": concentration,
            "dilution_factor": dilution_factor,
            "final_concentration_m": final_concentration
        },
        "x_values": factor_values,
        "y_values": concentration_values,
        "x_label": "Dilution Factor",
        "y_label": "Concentration (M)",
        "chart_title": "Solution Dilution Simulation"
    }

    return True, result