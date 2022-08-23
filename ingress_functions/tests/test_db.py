"""
Test db.py module
"""


from __app__.crop.constants import SQL_CONNECTION_STRING
from __app__.crop.db import (
    create_database,
    connect_db,
    drop_db,
    check_database_structure,
)


TEST_DB_NAME = "fake_db"


def test_create_database():

    # Test create new db
    created, log = create_database(SQL_CONNECTION_STRING, TEST_DB_NAME)
    assert created, log


def test_connect_db():

    # Try to connect to an engine that exists
    status, log, engine = connect_db(SQL_CONNECTION_STRING, TEST_DB_NAME)
    assert status, log

    # Try to connect to a db that does not exists:
    fake_db = "db_name_fake"
    status, log, engine = connect_db(SQL_CONNECTION_STRING, fake_db)
    assert status is False, log
    assert engine is None


def test_check_database_structure():

    status, log, engine = connect_db(SQL_CONNECTION_STRING, TEST_DB_NAME)
    assert status, log
    assert engine is not None

    good, log = check_database_structure(engine)
    assert good, log


def test_drop_db():

    # Test drop db
    success, log = drop_db(SQL_CONNECTION_STRING, TEST_DB_NAME)
    assert success, log
