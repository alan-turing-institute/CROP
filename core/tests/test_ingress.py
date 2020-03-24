"""
Module to test importing data from sensors to db
"""

import os
import pytest
import pandas as pd

from core.crop.db import create_database, connect_db
from core.crop.ingress import import_data
from core.crop.ingress_adv import advanticsys_import
from core.crop.populate_db import session_open, session_close, insert_advanticsys_data

from core.crop.structure import TypeClass, LocationClass, SensorClass

from core.crop.constants import (
    SQL_SERVER,
    SQL_USER,
    SQL_PASSWORD,
    SQL_HOST,
    SQL_PORT,
    CONST_ADVANTICSYS_DIR,
    CONST_ADVANTICSYS_TEST_1,
    CONST_COREDATA_DIR,
    SQL_CONNECTION_STRING
)


TEST_DB_NAME = "fake_db"

SENSOR_TYPE = "advanticsys" # FIXME:(name or id?)

file_path = os.path.join(CONST_ADVANTICSYS_DIR, CONST_ADVANTICSYS_TEST_1)

def test_create_database():
    """
    Tests creating a new database
    """

    created, log = create_database(SQL_CONNECTION_STRING, TEST_DB_NAME)
    assert created, log

def test_insert_type_data():
    """
    Tests bulk inserting test type data
    """

    test_csv = "Sensortypes.csv"

    type_df = pd.read_csv(os.path.join(CONST_COREDATA_DIR, test_csv))
    assert type_df.empty == False

    # Try to connect to an engine that exists
    status, log, engine = connect_db(SQL_CONNECTION_STRING, TEST_DB_NAME)
    assert status, log

    # Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)

    # Check if table is empty and bulk inserts if it is
    first_entry = session.query(TypeClass).first()
    if first_entry == None:
        session.bulk_insert_mappings(TypeClass, type_df.to_dict(orient="records"))
        assert session.query(TypeClass).count() == len(type_df.index)
    else:
        assert session.query(TypeClass).count() == len(type_df.index)


    session_close(session)

def test_insert_location_data():
    """
    Tests bulk inserting test location data
    """

    test_csv = "locations.csv"

    # test reading type data
    loc_df = pd.read_csv(os.path.join(CONST_COREDATA_DIR, test_csv))
    assert loc_df.empty == False

    # Try to connect to an engine that exists
    status, log, engine = connect_db(SQL_CONNECTION_STRING, TEST_DB_NAME)
    assert status, log

    # Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)

    # Check if table is empty and bulk inserts if it is
    first_entry = session.query(LocationClass).first()
    if first_entry == None:
        session.bulk_insert_mappings(LocationClass, loc_df.to_dict(orient="records"))
        assert session.query(LocationClass).count() == len(loc_df.index)
    else:
        assert session.query(LocationClass).count() == len(loc_df.index)

    session_close(session)

def test_insert_sensor_data():
    """
    Tests bulk inserting test sensor data
    """

    test_csv = "Sensors.csv"

    sensor_df = pd.read_csv(os.path.join(CONST_COREDATA_DIR, test_csv))
    assert sensor_df.empty == False

    # Try to connect to an engine that exists
    status, log, engine = connect_db(SQL_CONNECTION_STRING, TEST_DB_NAME)
    assert status, log

    # Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)

    # Check if table is empty and bulk inserts if it is
    first_entry = session.query(SensorClass).first()
    if first_entry == None:
        session.bulk_insert_mappings(SensorClass, sensor_df.to_dict(orient="records"))
        assert session.query(SensorClass).count() == len(sensor_df.index)
    else:
        assert session.query(SensorClass).count() == len(sensor_df.index)

    session_close(session)


def test_import_data ():

    # Bring df
    success, log, test_ingress_df = advanticsys_import(file_path)
    assert success, log
    assert isinstance(test_ingress_df, pd.DataFrame)

    # Test import function
    success, log = import_data (
        test_ingress_df,
        SENSOR_TYPE,
        SQL_SERVER,
        SQL_USER,
        SQL_PASSWORD,
        SQL_HOST,
        SQL_PORT,
        TEST_DB_NAME
    )
    assert success, log
