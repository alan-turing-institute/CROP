import pytest
import os
import sys
from pathlib import Path
import pandas as pd

file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from crop.sql import (
    advantix_SQL_insert
)

from crop.constants import (
    SQL_DBNAME,
    SQL_CONNECTION_STRING,
    CONST_TEST_DIR_DATA,
    CONST_ADVANTIX_TEST_1,
    ADVANTIX_READINGS_TABLE_NAME
)

from crop.create_db import (
    create_database,
    check_table_exists
)


def test_db_creation ():
    error, log = create_database(SQL_CONNECTION_STRING, SQL_DBNAME)
    print(log)
    assert error == False, log

def test_check_table_exists():

    conn_string = "{}{}".format(SQL_CONNECTION_STRING, SQL_DBNAME)

    table_name_list = [ADVANTIX_READINGS_TABLE_NAME] #reads the advantix tablename from constants
    for table_name in table_name_list:
        exists, _ = check_table_exists(conn_string, table_name)
        assert exists == True
    
    exists, error = check_table_exists(conn_string, "_")
    assert exists == False
    assert (len(error) > 0) == True

    exists, error = check_table_exists("REG SERVER", "_")
    assert exists == False
    assert (len(error) > 0) == True



#def test_check_database_structure ():
#    error, log = check_database_structure (SQL_CONNECTION_STRING, SQL_DBNAME)
#    assert error == False, log
    