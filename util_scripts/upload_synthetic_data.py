#!/usr/bin/env python
"""
Script that creates (if needed) a database in an existing PostgreSQL
server and uploads synthetic data to it.
"""
import os
import sys
import argparse
import json
import uuid
import pandas as pd

from core.structure import (
    LocationClass,
    TypeClass,
    SensorClass,
    SensorLocationClass,
    ReadingsAranetTRHClass,
    ReadingsAranetCO2Class,
    ReadingsAranetAirVelocityClass,
    CropTypeClass,
    BatchClass,
    BatchEventClass,
    HarvestClass,
    ModelClass,
    ModelMeasureClass,
    ModelScenarioClass,
    ReadingsWeatherClass,
    WeatherForecastsClass,
)

from core.constants import (
    CONST_TESTDATA_LOCATION_FOLDER,
    CONST_TESTDATA_SENSOR_FOLDER,
    CONST_TESTDATA_CROPGROWTH_FOLDER,
    CONST_TESTDATA_MODEL_FOLDER,
    LOCATION_CSV,
    SENSOR_CSV,
    SENSOR_TYPE_CSV,
    SENSOR_LOCATION_CSV,
    CROP_TYPE_CSV,
    BATCH_CSV,
    BATCH_EVENT_CSV,
    HARVEST_CSV,
    MODEL_CSV,
    MEASURE_CSV,
    SQL_TEST_CONNECTION_STRING,
)

from core.db import (
    create_database,
    connect_db,
    session_open,
    session_close,
)

from util_scripts.generate_synthetic_readings import (
    generate_trh_readings,
    generate_co2_readings,
    generate_airvelocity_readings,
    generate_weather,
    generate_weather_forecast,
)


def error_message(message):
    """
    Prints error message.

    """
    print(f"ERROR: {message}")
    sys.exit()


def insert_from_df(engine, df, DbClass):
    """
    Read a CSV file into a pandas dataframe, and then upload to
    database table

    Parameters
    ==========
    engine: SQL engine object
    df:pandas.DataFrame, input data
    DbClass:class from core.structure.py
    """
    assert not df.empty

    # Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)

    # Check if table is empty and bulk inserts if it is
    first_entry = session.query(DbClass).first()

    if first_entry is None:
        session.bulk_insert_mappings(DbClass, df.to_dict(orient="records"))
        session_close(session)

        assert session.query(DbClass).count() == len(df.index)
    else:
        session_close(session)

        assert session.query(DbClass).count() == len(df.index)
    session_close(session)
    print(f"Inserted {len(df.index)} rows to table {DbClass.__tablename__}")


def add_location_data(engine):
    # locations in the farm, used by both sensors and crops
    csv_location = os.path.join(CONST_TESTDATA_LOCATION_FOLDER, LOCATION_CSV)
    df = pd.read_csv(csv_location)
    insert_from_df(engine, df, LocationClass)


def add_sensor_data(engine):
    # sensor type
    csv_location = os.path.join(CONST_TESTDATA_SENSOR_FOLDER, SENSOR_TYPE_CSV)
    df = pd.read_csv(csv_location)
    insert_from_df(engine, df, TypeClass)
    # sensors
    csv_location = os.path.join(CONST_TESTDATA_SENSOR_FOLDER, SENSOR_CSV)
    df = pd.read_csv(csv_location)
    insert_from_df(engine, df, SensorClass)
    # sensor location
    csv_location = os.path.join(CONST_TESTDATA_SENSOR_FOLDER, SENSOR_LOCATION_CSV)
    df = pd.read_csv(csv_location)
    insert_from_df(engine, df, SensorLocationClass)
    # T/RH readings
    df = generate_trh_readings()
    insert_from_df(engine, df, ReadingsAranetTRHClass)
    # CO2 readings
    df = generate_co2_readings()
    insert_from_df(engine, df, ReadingsAranetCO2Class)
    # air velocity readings
    df = generate_airvelocity_readings()
    insert_from_df(engine, df, ReadingsAranetAirVelocityClass)


def add_weather_data(engine):
    # weather history
    df = generate_weather()
    insert_from_df(engine, df, ReadingsWeatherClass)
    # weather forecast
    df = generate_weather()
    insert_from_df(engine, df, WeatherForecastsClass)


def add_crop_data(engine):
    def _add_growapp_id(df):
        # add uuid column called 'growapp_id'
        df["growapp_id"] = [uuid.uuid4() for _ in range(len(df.index))]
        return df

    # crop type
    csv_location = os.path.join(CONST_TESTDATA_CROPGROWTH_FOLDER, CROP_TYPE_CSV)
    df = _add_growapp_id(pd.read_csv(csv_location))
    insert_from_df(engine, df, CropTypeClass)
    # batches
    csv_location = os.path.join(CONST_TESTDATA_CROPGROWTH_FOLDER, BATCH_CSV)
    df = _add_growapp_id(pd.read_csv(csv_location))
    insert_from_df(engine, df, BatchClass)
    # batch events
    csv_location = os.path.join(CONST_TESTDATA_CROPGROWTH_FOLDER, BATCH_EVENT_CSV)
    df = _add_growapp_id(pd.read_csv(csv_location))
    insert_from_df(engine, df, BatchEventClass)
    # harvests
    csv_location = os.path.join(CONST_TESTDATA_CROPGROWTH_FOLDER, HARVEST_CSV)
    df = _add_growapp_id(pd.read_csv(csv_location))
    insert_from_df(engine, df, HarvestClass)


def add_model_data(engine):
    csv_location = os.path.join(CONST_TESTDATA_MODEL_FOLDER, MODEL_CSV)
    df = pd.read_csv(csv_location)
    insert_from_df(engine, df, ModelClass)


def generate_scenarios(model_id):
    """
    Do a Cartesian product of the variables.
    """
    scenarios = []
    # default scenario
    scenario = {
        "model_id": model_id,
        "ventilation_rate": 2,
        "num_dehumidifiers": 2,
        "lighting_shift": 0,
        "lighting_on_duration": 16,
        "scenario_type": "BAU",
    }
    scenarios.append(scenario)
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
                    "scenario_type": "Test",
                }
                scenarios.append(scenario)
    df = pd.DataFrame(scenarios)
    return df


def add_scenario_data(engine):
    df = generate_scenarios(2)
    insert_from_df(engine, df, ModelScenarioClass)


def add_measure_data(engine):
    # get default measures
    #    csv_location = os.path.join(CONST_TESTDATA_MODEL_FOLDER, MEASURE_CSV)
    #    df = pd.read_csv(csv_location)
    #    measures = json.loads(df.to_json(orient="records"))
    # get extra ones from scenarios
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
    insert_from_df(engine, measures_df, ModelMeasureClass)


def main(db_name):
    """
    Main routine.

    Arguments:
        db_name: Database name
    """

    created, log = create_database(SQL_TEST_CONNECTION_STRING, db_name)

    if not created:
        error_message(log)

    # creating an engine
    status, log, engine = connect_db(SQL_TEST_CONNECTION_STRING, db_name)

    if not status:
        error_message(log)

    add_location_data(engine)
    add_sensor_data(engine)
    add_weather_data(engine)
    add_crop_data(engine)
    add_model_data(engine)
    add_scenario_data(engine)
    add_measure_data(engine)
