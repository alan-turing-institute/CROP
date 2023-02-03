#!/usr/bin/env python
"""
Script that uploads calibration model scenarios and corresponding measures
to the database
"""
import os
import sys
import argparse
import json
import uuid
import pandas as pd

from cropcore.structure import (
    SensorClass,
    ModelClass,
    ModelMeasureClass,
    ModelScenarioClass,
    ScenarioType,
)

from cropcore.constants import SQL_CONNECTION_STRING, SQL_DBNAME

from cropcore.db import (
    create_database,
    connect_db,
    session_open,
    session_close,
)

from cropcore.utils import insert_to_db_from_df

GES_MODEL_ID = 3


def error_message(message):
    """
    Prints error message.

    """
    print(f"ERROR: {message}")
    sys.exit()


def generate_scenarios(model_id):
    """
    Do a Cartesian product of the variables.
    """
    scenarios = []
    # default Business As Usual scenario
    scenario = {
        "model_id": model_id,
        "ventilation_rate": 2,
        "num_dehumidifiers": 2,
        "lighting_shift": 0,
        "lighting_on_duration": 16,
        "scenario_type": ScenarioType.BAU,
    }
    scenarios.append(scenario)
    # Test scenarios
    lighting_on_duration = 16
    for ventilation_rate in range(2, 12, 2):
        for num_dehumidifiers in range(3):
            for lighting_shift in range(-6, 9, 3):
                #                for lighting_on_duration in range(12, 22, 2):
                scenario = {
                    "model_id": model_id,
                    "ventilation_rate": float(ventilation_rate),
                    "num_dehumidifiers": num_dehumidifiers,
                    "lighting_shift": float(lighting_shift),
                    "lighting_on_duration": float(lighting_on_duration),
                    "scenario_type": ScenarioType.Test,
                }
                scenarios.append(scenario)
    df = pd.DataFrame(scenarios)
    return df


def add_scenario_data(model_id, engine):
    df = generate_scenarios(model_id)
    insert_to_db_from_df(engine, df, ModelScenarioClass)


def add_measure_data(model_id, engine):

    measures = []
    scenarios_df = generate_scenarios(2)
    for i, row in scenarios_df.iterrows():

        if row.scenario_type == "BAU":  # Business As Usual
            measure_names = [
                "Mean Temperature (Degree Celcius)",
                "Upper Bound Temperature (Degree Celcius)",
                "Lower Bound Temperature (Degree Celcius)",
                "Mean Relative Humidity (Percent)",
                "Upper Bound Relative Humidity (Percent)",
                "Lower Bound Relative Humidity (Percent)",
            ]
        else:
            measure_names = [
                "Mean Temperature (Degree Celcius)",
                "Mean Relative Humidity (Percent)",
            ]
        for measure_name in measure_names:
            measure = {
                "measure_name": measure_name,
                "measure_description": "",
                "scenario_id": i + 1,  # because the IDs start counting at 1
            }
            measures.append(measure)
    measures_df = pd.DataFrame(measures)
    insert_to_db_from_df(engine, measures_df, ModelMeasureClass)


def main():
    """
    Upload the GES model scenarios and corresponding measures.
    """

    # creating an engine
    status, log, engine = connect_db(SQL_CONNECTION_STRING, SQL_DBNAME)

    if not status:
        error_message(log)

    add_scenario_data(GES_MODEL_ID, engine)
    add_measure_data(GES_MODEL_ID, engine)


if __name__ == "__main__":
    main()
