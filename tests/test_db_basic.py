"""
Test db.py module
"""
import pytest

from core.constants import SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME

from core.db import (
    connect_db,
    check_database_structure,
)

from .conftest import check_for_docker


DOCKER_RUNNING = check_for_docker()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_connect_db():

    # Try to connect to an engine that exists
    status, log, engine = connect_db(SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME)
    assert status, log

    # Try to connect to a db that does not exists:
    fake_db = "db_name_fake"
    status, log, engine = connect_db(SQL_TEST_CONNECTION_STRING, fake_db)
    assert status is False, log
    assert engine is None


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_check_database_structure():

    status, log, engine = connect_db(SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME)
    assert status, log
    assert engine is not None

    good, log = check_database_structure(engine)
    assert good, log
