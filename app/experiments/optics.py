NAME = "Thin Lens"

DESCRIPTION = (
    "Calculate image distance using "
    "object distance and focal length."
)

EQUIPMENT = "Optics Workstation"

FIELDS = (
    "Object Distance (cm):",
    "Focal Length (cm):"
)


def run(first_value, second_value):
    try:
        object_distance = float(first_value)
        focal_length = float(second_value)

    except ValueError:
        return False, "Object distance and focal length must be numbers."

    if object_distance <= 0:
        return False, "Object distance must be greater than zero."

    if focal_length <= 0:
        return False, "Focal length must be greater than zero."

    if object_distance == focal_length:
        return False, "Object distance cannot equal focal length."

    image_distance = (
        focal_length
        * object_distance
        / (
            object_distance
            - focal_length
        )
    )

    object_values = [
        focal_length + index + 1
        for index in range(40)
    ]

    image_values = [
        (
            focal_length
            * distance
            / (
                distance
                - focal_length
            )
        )
        for distance in object_values
    ]

    result = {
        "experiment_name": NAME,
        "summary": (
            "Calculated Image Distance: "
            f"{image_distance:.3f} cm"
        ),
        "record": {
            "object_distance_cm": object_distance,
            "focal_length_cm": focal_length,
            "image_distance_cm": image_distance
        },
        "x_values": object_values,
        "y_values": image_values,
        "x_label": "Object Distance (cm)",
        "y_label": "Image Distance (cm)",
        "chart_title": "Thin Lens Simulation"
    }

    return True, result