"""
Module to test importing data from sensors to db
"""

import os
import pandas as pd

from __app__.crop.ingress import import_data
from __app__.crop.ingress_adv import advanticsys_import

from __app__.crop.constants import (
    SQL_USER,
    SQL_PASSWORD,
    SQL_HOST,
    SQL_PORT,
    CONST_ADVANTICSYS,
    CONST_ADVANTICSYS_DIR,
    CONST_ADVANTICSYS_TEST_1,
    SQL_TEST_DBNAME
)

def test_import_data():
    """
    unit test for import_data
    """

    file_path = os.path.join(CONST_ADVANTICSYS_DIR, CONST_ADVANTICSYS_TEST_1)

    # Bring df
    success, log, test_ingress_df = advanticsys_import(file_path)
    assert success, log
    assert isinstance(test_ingress_df, pd.DataFrame)

    # Test import function
    success, log = import_data(
        test_ingress_df,
        CONST_ADVANTICSYS,
        SQL_USER,
        SQL_PASSWORD,
        SQL_HOST,
        SQL_PORT,
        SQL_TEST_DBNAME
    )

    assert success is False, log == "Cannot insert 75 duplicate values"
