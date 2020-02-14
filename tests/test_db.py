import pytest


from crop.constants import (
    SQL_DBNAME,
    SQL_CONNECTION_STRING,
)

from crop.db import (
    create_database,
    connect_db,
    drop_db,
    check_database_structure
)

test_db_name = "test_drop"

@pytest.mark.order1
def test_create_database():

    #Test create new db
    created, log = create_database(SQL_CONNECTION_STRING, test_db_name)
    assert created, log

@pytest.mark.order2
def test_connect_db():
    
    # Try to connect to an engine that exists
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log
    
    #Try to connect to a db that does not exists:
    fake_db = "db_name_fake"
    status, log, engine = connect_db(SQL_CONNECTION_STRING, fake_db)
    assert status == False, log
    assert engine == None

@pytest.mark.order3
def test_check_database_structure():

    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log
    assert engine != None

    good, log = check_database_structure(engine)
    assert good, log

@pytest.mark.order4
def test_drop_db():

    #Test create new db
    success, log = drop_db(SQL_CONNECTION_STRING, test_db_name)
    assert success, log