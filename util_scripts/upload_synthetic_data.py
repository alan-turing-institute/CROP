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

from cropcore.structure import (
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

from cropcore.db import (
    create_database,
    connect_db,
    session_open,
    session_close,
)

from cropcore.utils import insert_to_db_from_df

from util_scripts.generate_synthetic_readings import (
    generate_trh_readings,
    generate_co2_readings,
    generate_airvelocity_readings,
    generate_weather,
    generate_weather_forecast,
)

from util_scripts.upload_model_scenarios_measures import (
    add_scenario_data,
    add_measure_data,
)


def error_message(message):
    """
    Prints error message.

    """
    print(f"ERROR: {message}")
    sys.exit()


def add_location_data(engine):
    # locations in the farm, used by both sensors and crops
    csv_location = os.path.join(CONST_TESTDATA_LOCATION_FOLDER, LOCATION_CSV)
    df = pd.read_csv(csv_location)
    insert_to_db_from_df(engine, df, LocationClass)


def add_sensor_data(engine):
    # sensor type
    csv_location = os.path.join(CONST_TESTDATA_SENSOR_FOLDER, SENSOR_TYPE_CSV)
    df = pd.read_csv(csv_location)
    insert_to_db_from_df(engine, df, TypeClass)
    # sensors
    csv_location = os.path.join(CONST_TESTDATA_SENSOR_FOLDER, SENSOR_CSV)
    df = pd.read_csv(csv_location)
    insert_to_db_from_df(engine, df, SensorClass)
    # sensor location
    csv_location = os.path.join(CONST_TESTDATA_SENSOR_FOLDER, SENSOR_LOCATION_CSV)
    df = pd.read_csv(csv_location)
    insert_to_db_from_df(engine, df, SensorLocationClass)
    # T/RH readings
    df = generate_trh_readings()
    insert_to_db_from_df(engine, df, ReadingsAranetTRHClass)
    # CO2 readings
    df = generate_co2_readings()
    insert_to_db_from_df(engine, df, ReadingsAranetCO2Class)
    # air velocity readings
    df = generate_airvelocity_readings()
    insert_to_db_from_df(engine, df, ReadingsAranetAirVelocityClass)


def add_weather_data(engine):
    # weather history
    df = generate_weather()
    insert_to_db_from_df(engine, df, ReadingsWeatherClass)
    # weather forecast
    df = generate_weather()
    insert_to_db_from_df(engine, df, WeatherForecastsClass)


def add_crop_data(engine):
    def _add_growapp_id(df):
        # add uuid column called 'growapp_id'
        df["growapp_id"] = [uuid.uuid4() for _ in range(len(df.index))]
        return df

    # crop type
    csv_location = os.path.join(CONST_TESTDATA_CROPGROWTH_FOLDER, CROP_TYPE_CSV)
    df = _add_growapp_id(pd.read_csv(csv_location))
    insert_to_db_from_df(engine, df, CropTypeClass)
    # batches
    csv_location = os.path.join(CONST_TESTDATA_CROPGROWTH_FOLDER, BATCH_CSV)
    df = _add_growapp_id(pd.read_csv(csv_location))
    insert_to_db_from_df(engine, df, BatchClass)
    # batch events
    csv_location = os.path.join(CONST_TESTDATA_CROPGROWTH_FOLDER, BATCH_EVENT_CSV)
    df = _add_growapp_id(pd.read_csv(csv_location))
    insert_to_db_from_df(engine, df, BatchEventClass)
    # harvests
    csv_location = os.path.join(CONST_TESTDATA_CROPGROWTH_FOLDER, HARVEST_CSV)
    df = _add_growapp_id(pd.read_csv(csv_location))
    insert_to_db_from_df(engine, df, HarvestClass)


def add_model_data(engine):
    csv_location = os.path.join(CONST_TESTDATA_MODEL_FOLDER, MODEL_CSV)
    df = pd.read_csv(csv_location)
    insert_to_db_from_df(engine, df, ModelClass)


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
    # GES model ID for tests is 2
    add_scenario_data(2, engine)
    add_measure_data(2, engine)
