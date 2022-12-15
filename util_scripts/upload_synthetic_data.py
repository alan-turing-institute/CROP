#!/usr/bin/env python
"""
Script that creates (if needed) a database in an existing PostgreSQL
server and uploads synthetic data to it.
"""

import argparse

import os
import sys
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
)

from core.constants import (
    CONST_TESTDATA_LOCATION_FOLDER,
    CONST_TESTDATA_SENSOR_FOLDER,
    CONST_TESTDATA_CROPGROWTH_FOLDER,
    LOCATION_CSV,
    SENSOR_CSV,
    SENSOR_TYPE_CSV,
    SENSOR_LOCATION_CSV,
    CROP_TYPE_CSV,
    BATCH_CSV,
    BATCH_EVENT_CSV,
    HARVEST_CSV,
    SQL_CONNECTION_STRING,
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


def main(db_name):
    """
    Main routine.

    Arguments:
        db_name: Database name
    """

    created, log = create_database(SQL_CONNECTION_STRING, db_name)

    if not created:
        error_message(log)

    # creating an engine
    status, log, engine = connect_db(SQL_CONNECTION_STRING, db_name)

    if not status:
        error_message(log)

    add_location_data(engine)
    add_sensor_data(engine)
    add_crop_data(engine)
