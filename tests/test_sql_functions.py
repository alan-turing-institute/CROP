import pytest
import os
import sys
from pathlib import Path
import pandas as pd


file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from crop.populate_db import (
    bulk_insert_df
    )

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


def test_bulk_insert_df ():

    conn_string = "{}{}".format(SQL_CONNECTION_STRING, SQL_DBNAME)

    table_name_list = [ADVANTIX_READINGS_TABLE_NAME] #reads the advantix tablename from constants
    for table_name in table_name_list:
        exists, _ = check_table_exists(conn_string, table_name)
        assert exists == True