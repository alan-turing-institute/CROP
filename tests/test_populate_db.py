"""
Module to test creating a database and populating it with
test sensor, sensor type, location and advantix data.
"""

import os
import pytest
import pandas as pd


from crop.structure import(
    Type,
    Location,
    Sensor
    )

from crop.constants import(
    CONST_COREDATA_DIR,
    CONST_ADVANTIX_DIR,
    CONST_ADVANTIX_TEST_1,
    CONST_ADVANTIX_TEST_10,
    SQL_CONNECTION_STRING,
)

from crop.db import(
    create_database,
    connect_db,
    drop_db
)

from crop.ingress import(
    advantix_import
)

from crop.populate_db import(
    session_open,
    session_close,
    insert_advantix_data
)

# Test database name
test_db_name = "fake_db1"

@pytest.mark.order1
def test_create_database():
    """
    Tests creating a new database
    """
    created, log = create_database(SQL_CONNECTION_STRING, test_db_name)
    assert created, log

@pytest.mark.order2
def test_insert_type_data():
    """
    Tests bulk inserting test type data
    """
    test_csv = "Sensortypes.csv"

    type_df = pd.read_csv(os.path.join(CONST_COREDATA_DIR, test_csv))
    assert type_df.empty == False

    # Try to connect to an engine that exists
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log

    #Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)
    
    # Check if table is empty and bulk inserts if it is
    first_entry = session.query(Type).first()
    if first_entry == None: 
        session.bulk_insert_mappings(Type, type_df.to_dict(orient='records'))
        assert session.query(Type).count() == len(type_df.index)
    else:
        assert session.query(Type).count() == len(type_df.index)

    session_close(session)

@pytest.mark.order3
def test_insert_sensor_data():
    """
    Tests bulk inserting test sensor data
    """

    test_csv = "Sensors.csv"

    sensor_df = pd.read_csv(os.path.join(CONST_COREDATA_DIR, test_csv))
    assert sensor_df.empty == False

    # Try to connect to an engine that exists
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log

    #Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)

    # Check if table is empty and bulk inserts if it is
    first_entry = session.query(Sensor).first()
    if first_entry == None: 
        session.bulk_insert_mappings(Sensor, sensor_df.to_dict(orient='records'))
        assert session.query(Sensor).count() == len(sensor_df.index)
    else:
        assert session.query(Sensor).count() == len(sensor_df.index)

    session_close(session)

@pytest.mark.order4
def test_insert_location_data():
    """
    Tests bulk inserting test location data
    """

    test_csv = "Locations.csv"

    #test reading type data
    loc_df = pd.read_csv(os.path.join(CONST_COREDATA_DIR, test_csv))
    assert loc_df.empty == False

    # Try to connect to an engine that exists
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log

    #Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)

    # Check if table is empty and bulk inserts if it is
    first_entry = session.query(Location).first()
    if first_entry == None: 
        session.bulk_insert_mappings(Location, loc_df.to_dict(orient='records'))
        assert session.query(Location).count() == len(loc_df.index)
    else:
        assert session.query(Location).count() == len(loc_df.index)

    session_close(session)

@pytest.mark.order5
def test_insert_advantix_data():
    """
    Tests  add inserting test advantix data
    """

    file_path = os.path.join(CONST_ADVANTIX_DIR, CONST_ADVANTIX_TEST_1)
    success, log, test_ingress_df = advantix_import(file_path)
    assert success, log
    assert isinstance(test_ingress_df, pd.DataFrame)

    # Try to connect to an engine that exists
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log

    #Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)
    #stest loading sensor data to db
    success, log = insert_advantix_data(session, test_ingress_df)
    assert success, log

    file_path = os.path.join(CONST_ADVANTIX_DIR, CONST_ADVANTIX_TEST_10)
    success, log, test_ingress_df = advantix_import(file_path)
    assert success, log
    assert isinstance(test_ingress_df, pd.DataFrame)

    success, log = insert_advantix_data(session, test_ingress_df)
    assert success, log

    session_close(session)
