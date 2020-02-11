import pytest
import os
import sys
import pandas as pd

from sqlalchemy import create_engine

from crop.constants import (
    SQL_DBNAME,
    SQL_CONNECTION_STRING,
    CONST_TEST_DIR_DATA,
    CONST_ADVANTIX_TEST_1,
    ADVANTIX_READINGS_TABLE_NAME
)

from crop.create_db import (
    create_database,
    check_database_structure
)

def test_create_database():

    test_db_name = "test_db_2"
    test_db_name_bad = "test_db_bad"
    created, log = create_database(SQL_CONNECTION_STRING, test_db_name)
    assert created, log

    # TODO: check if the structure is correct
    db_conn_string = "{}{}".format(SQL_CONNECTION_STRING, test_db_name)
    engine = create_engine(db_conn_string)

    good, log = check_database_structure(engine)
    assert good, log

     # TODO: check if the structure is correct
    db_conn_string = "{}{}".format(SQL_CONNECTION_STRING, test_db_name_bad)
    engine = create_engine(db_conn_string)

    # FIXME: should be none
    assert(engine == None)

    # TODO: needs a function to drop test database


# TODO: write a test for check_database_structure where structure is incorrect
# TODO: write a test for connect_db
