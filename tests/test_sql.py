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
    CONST_ADVANTIX_FOLDER,
    CONST_ADVANTIX_TEST_1,
    CONST_ADVANTIX_TEST_2
)

from crop.create_db import create_database


def test_db_creation ():
    error, log = create_database(SQL_CONNECTION_STRING, SQL_DBNAME)
    assert error == False, log


def test_db_connection ():
    try: 
        engine = create_engine(SQL_CONNECTION_STRING + SQL_DBNAME)
    except:
        error = True
        log = "Error connecting to the database"
        return error, log



    

    # # Test dataframe
    # file_path = os.path.join(CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_1)
    # data_df = advantix_read_csv(file_path)
    # # counting the number of entries
    # assert (len(data_df.index) == 75)

    # result, error = advantix_SQL_insert(data_df, None, None, None, None, None)


    assert(result)