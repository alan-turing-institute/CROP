import pytest
import pandas as pd
from sqlalchemy.orm import sessionmaker, relationship

from crop.structure import(
    Type,
    Location,
    Sensor
    )

from crop.constants import (
    SQL_DBNAME,
    CONST_COREDATA_DIR,
    CONST_ADVANTIX_DIR,
    CONST_ADVANTIX_TEST_1,
    SQL_CONNECTION_STRING
)
from crop.db import (
    connect_db
)

from crop.populate_db import (
    session_open,
    session_close,
    insert_type_data,
    insert_sensor_data,
    insert_location_data,
    insert_advantix_data
)


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


def test_insert_type_data():
    
    test_csv = "Sensortypes.csv"
    
    #test reading type data
    success, log, type_df = read_core_csv("%s\\%s" % (CONST_COREDATA_DIR, test_csv))
    assert success, log
    assert type_df.empty == False

    # Try to connect to an engine that exists
    test_db_name = SQL_DBNAME
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log

    #Creates/Opens a new connection to the db and binds the engine
    session = session_open (engine)
    insert_type_data (session, type_df)
    session_close (session)

def test_insert_sensor_data():
    
    test_csv = "Sensors.csv"
    
    #test reading type data
    success, log, sensor_df = read_core_csv("%s\\%s" % (CONST_COREDATA_DIR, test_csv))
    assert success, log
    assert sensor_df.empty == False

    # Try to connect to an engine that exists
    test_db_name = SQL_DBNAME
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log

     #Creates/Opens a new connection to the db and binds the engine
    session = session_open (engine)
    #test loading sensor data to db
    insert_sensor_data (session, sensor_df)  
    session_close (session)
   
def test_insert_location_data():
    
    test_csv = "Locations.csv"
    
    #test reading type data
    success, log, df = read_core_csv("%s\\%s" % (CONST_COREDATA_DIR, test_csv))
    assert success, log
    assert df.empty == False

    # Try to connect to an engine that exists
    test_db_name = SQL_DBNAME
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log

    #Creates/Opens a new connection to the db and binds the engine
    session = session_open (engine)
    #test loading sensor data to db
    insert_location_data (session, df)  
    session_close (session)
   
def test_insert_advantix_data():
    #TODO: PUT THE ADVANTIX INGRESS DATA
    test_csv = CONST_ADVANTIX_TEST_1
    
    #test reading type data
    success, log, df = read_core_csv("%s\\%s" % (CONST_ADVANTIX_DIR, test_csv))
    assert success, log
    assert df.empty == False

    # Try to connect to an engine that exists
    test_db_name = SQL_DBNAME
    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
    assert status, log

    #Creates/Opens a new connection to the db and binds the engine
    session = session_open (engine)
    #test loading sensor data to db
    insert_advantix_data (session, df)
    session_close (session)

test_insert_advantix_data()
#test_insert_type_data()
#test_insert_sensor_data()
#test_insert_location_data()

#def test_load_location_data ():
    
#    locations_test_csv = "locations.csv"
    
#    #test reading type data
#    success, log, type_df = read_core_csv("%s\\%s" % (CONST_COREDATA_DIR, locations_test_csv))
#    assert success, log
#    assert type_df.empty == False

#    # Try to connect to an engine that exists
#    test_db_name = "test_db_3"
#    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
#    assert status, log

#    #test loading type data to db
#    bulk_update_df (engine, type_df, Location)

#def test_load_sensor_data ():
    
#    sensors_test_csv = "Sensors.csv"
    
#    #test reading type data
#    success, log, type_df = read_core_csv("%s\\%s" % (CONST_COREDATA_DIR, sensors_test_csv))
#    assert success, log
#    assert type_df.empty == False

#    # Try to connect to an engine that exists
#    test_db_name = "test_db_3"
#    status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
#    assert status, log

#    #test loading type data to db
#    bulk_update_df (engine, type_df, Sensor)

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