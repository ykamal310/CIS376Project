import importlib.util
import json
import sys

from datetime import datetime
from pathlib import Path

from app.database import (
    get_or_create_experiment,
    save_experiment_result,
    sync_equipment_catalog
)


if getattr(sys, "frozen", False):
    EXPERIMENT_FOLDER = (
        Path(sys.executable).resolve().parent
        / "experiments"
    )
else:
    EXPERIMENT_FOLDER = (
        Path(__file__).resolve().parent
        / "experiments"
    )


def discover_experiments():
    modules = []

    if not EXPERIMENT_FOLDER.exists():
        return modules

    for file_path in EXPERIMENT_FOLDER.glob(
        "*.py"
    ):
        if file_path.name.startswith("_"):
            continue

        try:
            module_name = (
                "remote_lab_experiment_"
                f"{file_path.stem}"
            )

            spec = importlib.util.spec_from_file_location(
                module_name,
                file_path
            )

            if not spec or not spec.loader:
                continue

            module = importlib.util.module_from_spec(
                spec
            )

            spec.loader.exec_module(
                module
            )

            module.NAME
            module.DESCRIPTION
            module.EQUIPMENT
            module.FIELDS
            module.run

            modules.append(
                module
            )

        except Exception as error:
            print(
                f"Could not load experiment "
                f"{file_path.name}: {error}"
            )

    return modules


def sync_experiment_catalog():
    modules = discover_experiments()

    equipment_names = [
        module.EQUIPMENT
        for module in modules
    ]

    sync_equipment_catalog(
        equipment_names
    )

    for module in modules:
        get_or_create_experiment(
            module.NAME,
            module.DESCRIPTION
        )

    return len(modules)


def load_experiments():
    experiments = {}

    modules = discover_experiments()

    for module in modules:
        experiment_id = get_or_create_experiment(
            module.NAME,
            module.DESCRIPTION
        )

        experiments[module.NAME] = {
            "id": experiment_id,
            "name": module.NAME,
            "description": module.DESCRIPTION,
            "equipment": module.EQUIPMENT,
            "fields": module.FIELDS,
            "module": module
        }

    return experiments


def get_available_experiments(
    equipment_name
):
    experiments = load_experiments()

    available = []

    for experiment in experiments.values():
        if (
            experiment["equipment"]
            == equipment_name
        ):
            available.append(
                experiment
            )

    return available


def get_experiment_fields(
    experiment_name
):
    experiments = load_experiments()

    experiment = experiments.get(
        experiment_name
    )

    if not experiment:
        return (
            "First Value:",
            "Second Value:"
        )

    return experiment["fields"]


def run_experiment(
    experiment_name,
    first_value,
    second_value
):
    experiments = load_experiments()

    experiment = experiments.get(
        experiment_name
    )

    if not experiment:
        return (
            False,
            "The selected experiment is not available."
        )

    return experiment["module"].run(
        first_value,
        second_value
    )


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