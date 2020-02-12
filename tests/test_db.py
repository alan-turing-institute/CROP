import pytest
import os
import sys
from sqlalchemy import create_engine
import pandas as pd

#resolve paths
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))


from crop.constants import (
    SQL_DBNAME,
    SQL_CONNECTION_STRING,
    CONST_TEST_DIR_DATA,
    CONST_ADVANTIX_TEST_1,
    ADVANTIX_READINGS_TABLE_NAME
)

from crop.db import (
    create_database,
    connect_db,
    drop_db,
    check_database_structure
)


def test_create_database():

    test_db_name = "test_db_3"
    test_db_name_bad = "test_db_bad" #fixed in the constant doesnt allow witespace or capital
    
    #Test create new db
    created, log = create_database(SQL_CONNECTION_STRING, test_db_name)
    assert created, log


def test_connect_db ():
    
    # Try to connect to an engine that exists
    test_db_name = "test_db_3"
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log
    
    #Try to connect to a db that does not exists:
    test_db_name_noexists = "test_db_noexists"
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name_noexists)
    assert (status == False), log
    assert engine == None

# TODO: needs a function to drop test database

def test_drop_db ():
    test_db_name = "crop_3"
    drop_db (SQL_CONNECTION_STRING, test_db_name)

# TODO: write a test for check_database_structure where structure is incorrect
# TODO: write a test for connect_db

def test_check_database_structure():
    
    test_db_name = "test_db_3"
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log
    assert engine != None

    good, log = check_database_structure(engine)
    assert good, log

     # TODO: check if the structure is correct (DONE)


    # FIXME: should be none (DONE)
    #assert(engine == None)

 