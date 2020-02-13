import pytest
import os
import sys
import pandas as pd

#resolve paths
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))


import crop.structure as structure

from crop.constants import (
    CONST_COREDATA_DIR,
    SQL_CONNECTION_STRING
)
from crop.db import (
    connect_db
)

from crop.populate_db import (
    merge_df,
)

# TODO: upload test data to the database

def read_core_csv(csv_path):
    """
    Reads and loads csv data to a pandas df. 
    Used to load the synthetic core data such as sensors or locations.  
    """
    print (csv_path)
    try:
        df= pd.read_csv(csv_path)
        #print (df.head(n=2))
    except:
        return False, "Error reading csv with path: %s" % csv_path, None
    
    return True, "", df


def test_load_type_data ():
    
    sensortype_test_csv = "Sensortypes.csv"
    
    #test reading type data
    success, log, df = read_core_csv("%s\\%s" % (CONST_COREDATA_DIR, sensortype_test_csv))
    assert success, log
    assert df.empty == False

    # Try to connect to an engine that exists
    test_db_name = "test_db_3"
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log

    Class = structure.Type
    #test loading type data to db
    merge_df (engine, df, Class)

test_load_type_data ()

#def test_check_sensor_exists():
    
#    created, log = create_database(SQL_CONNECTION_STRING, SQL_DBNAME)
#    assert created, log



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