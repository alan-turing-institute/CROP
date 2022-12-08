"""
Test db.py module
"""


from core.constants import SQL_CONNECTION_STRING, SQL_TEST_DBNAME

from core.db import (
    connect_db,
    check_database_structure,
)


def test_connect_db():

    # Try to connect to an engine that exists
    status, log, engine = connect_db(SQL_CONNECTION_STRING, SQL_TEST_DBNAME)
    assert status, log

    # Try to connect to a db that does not exists:
    fake_db = "db_name_fake"
    status, log, engine = connect_db(SQL_CONNECTION_STRING, fake_db)
    assert status is False, log
    assert engine is None


def test_check_database_structure():

    status, log, engine = connect_db(SQL_CONNECTION_STRING, SQL_TEST_DBNAME)
    assert status, log
    assert engine is not None

    good, log = check_database_structure(engine)
    assert good, log
