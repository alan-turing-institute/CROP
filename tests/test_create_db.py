import pytest
import os
import sys
from pathlib import Path
import pandas as pd

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

from crop.create_db import (
    create_database,
    check_table_exists,
    check_database_structure
)

def test_db_connection ():
    created, log, engine = connect_database(SQL_CONNECTION_STRING, SQL_DBNAME)
    assert created, log

#def test_check_table_exists():

#    conn_string = "{}{}".format(SQL_CONNECTION_STRING, SQL_DBNAME)

#    table_name_list = [ADVANTIX_READINGS_TABLE_NAME] #reads the advantix tablename from constants
#    for table_name in table_name_list:
#        exists, log = check_table_exists(conn_string, table_name)
#        assert exists, log
    
#    exists, log = check_table_exists(conn_string, "_")
#    assert exists, log

#    exists, error = check_table_exists("REG SERVER", "_")
#    assert exists == False


def test_check_database_structure():

    conn_string = "{}{}".format(SQL_CONNECTION_STRING, SQL_DBNAME)
    
    exists, log = check_database_structure (conn_string)
    assert exists, log
