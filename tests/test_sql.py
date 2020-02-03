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
    CONST_TEST_DIR_DATA,
    CONST_ADVANTIX_FOLDER,
    CONST_ADVANTIX_TEST_1,
    CONST_ADVANTIX_TEST_2
)

from crop.ingress import advantix_read_csv

from crop.create_db import create_database


def test_db_creation ():
    success, error = create_database(SQL_DBNAME)
    assert(success == True)
    assert(len(error) == 0)

def test_db_connection ():
    result, error= database_exists(SQL_CONNECTION_STRING_CROP), "database does not exist"
    assert(result == False)
    assert(len(error) > 0)


def test_advantix_SQL_insert():

    # Check for non existing dataframe
    data_df = None
    result, error = advantix_SQL_insert(data_df, None, None, None, None, None)
    assert(result == False)
    assert(len(error) > 0)

    # Check for empty dataframe
    data_df = pd.DataFrame()
    result, error = advantix_SQL_insert(data_df, None, None, None, None, None)
    assert(result == False)
    assert(len(error) > 0)

    # Test wrong structure
    file_path = os.path.join(CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_2)
    data_df = advantix_read_csv(file_path)
    result, error = advantix_SQL_insert(data_df, None, None, None, None, None)
    assert(result == False)
    assert(len(error) > 0)

    

    # # Test dataframe
    # file_path = os.path.join(CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_1)
    # data_df = advantix_read_csv(file_path)
    # # counting the number of entries
    # assert (len(data_df.index) == 75)

    # result, error = advantix_SQL_insert(data_df, None, None, None, None, None)


    assert(result)