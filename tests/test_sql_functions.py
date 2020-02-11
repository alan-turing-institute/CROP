import pytest
import os
import sys
import pandas as pd

from crop.populate_db import (
    bulk_insert_df
    )

from crop.create_db import (
    create_database
)

from crop.sql_functions import {
    check_sensor_exists
}

import crop.structure as structure

from crop.constants import (
    SQL_DBNAME,
    SQL_CONNECTION_STRING,
    CONST_TEST_DIR_DATA,
    CONST_ADVANTIX_TEST_1,
    ADVANTIX_READINGS_TABLE_NAME,
    CONST_ADVANTIX_FOLDER
)

def test_check_sensor_exists():
    
    created, log = create_database(SQL_CONNECTION_STRING, SQL_DBNAME)
    assert created, log

    # TODO: upload test data to the database
    

    check_sensor_exists()

    # TODO: drop database


# def test_advantix_bulk_insert_df ():
    
#     created, log = create_database(SQL_CONNECTION_STRING, SQL_DBNAME)
#     assert created, log

#     conn_string = "{}{}".format(SQL_CONNECTION_STRING, SQL_DBNAME)

#     table_name_list = [ADVANTIX_READINGS_TABLE_NAME] #reads the advantix tablename from constants
#     for table_name in table_name_list:
#         exists, _ = check_table_exists(conn_string, table_name)
#         assert exists == True

    # file_path = os.path.join(CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_1)
    # advantix_df = advantix_read_csv(file_path)

 #   engine = create_engine(conn_string)



    # bulk_insert_df(engine, advantix_df, structure.Readings_Advantix)


    # TODO: drop database 

# def test_merge_df ():
#     Data = merge_df(engine, Data, Class)