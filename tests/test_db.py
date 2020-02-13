import pytest


from ..crop.constants import (
    SQL_DBNAME,
    SQL_CONNECTION_STRING,
)

from ..crop.db import (
    create_database,
    connect_db,
    drop_db,
    check_database_structure
)

def test_create_database():

    test_db_name = SQL_DBNAME

    #Test create new db
    created, log = create_database(SQL_CONNECTION_STRING, test_db_name)
    assert created, log


def test_connect_db():
    
    # Try to connect to an engine that exists
    test_db_name = SQL_DBNAME
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log
    
    #Try to connect to a db that does not exists:
    fake_db = "db_name_fake"
    status, log, engine = connect_db(SQL_CONNECTION_STRING, fake_db)
    assert status == False, log
    assert engine == None

def test_drop_db():

    test_db_name = SQL_DBNAME
    success, log = drop_db(SQL_CONNECTION_STRING, test_db_name)
    assert success, log

def test_check_database_structure():

    test_db_name = SQL_DBNAME
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log
    assert engine != None

    good, log = check_database_structure(engine)
    assert good, log
