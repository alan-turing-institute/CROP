import pytest
import pandas as pd
import os
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
    SQL_CONNECTION_STRING,
)
from crop.db import (
    connect_db
)
from crop.ingress import (
    advantix_import
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
    
    file_path = os.path.join(CONST_ADVANTIX_DIR, CONST_ADVANTIX_TEST_1)
    success,log,test_ingress_df = advantix_import(file_path)
    assert success, log

    if isinstance(test_ingress_df, pd.DataFrame):
        # Try to connect to an engine that exists
        test_db_name = SQL_DBNAME
        status, log, engine = connect_db(SQL_CONNECTION_STRING, test_db_name)
        assert status, log

        #Creates/Opens a new connection to the db and binds the engine
        session = session_open (engine)
        #stest loading sensor data to db
        success, log = insert_advantix_data (session, test_ingress_df)
        assert success, log

        session_close (session)
    else: 
        print("its not a dataframe")
    
    

#test_insert_advantix_data()
#test_insert_type_data()
#test_insert_sensor_data()
#test_insert_location_data()
