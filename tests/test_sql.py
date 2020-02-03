import pytest
import os
import pandas as pd

from ..crop.sql import (
    advantix_SQL_insert
)

from ..crop.constants import (
    CONST_TEST_DIR_DATA,
    CONST_ADVANTIX_FOLDER,
    CONST_ADVANTIX_TEST_1,
    CONST_ADVANTIX_TEST_2
)

from ..crop.ingress import advantix_read_csv

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