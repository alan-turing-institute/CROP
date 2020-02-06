"""
Python module to perform data ingress operations

"""

import pandas as pd
from sqlalchemy import create_engine
from crop.ingress import advantix_df_checks
from crop.create_db import create_database
from crop.constants import (
    SQL_DBNAME,
    SQL_CONNECTION_STRING,
    CONST_ADVANTIX_TEST_1,
    CONST_COREDATA_DIR,
    SENSOR_CSV,
    SENSOR_TYPE_CSV
)
from crop.sql_functions import (
    bulk_insert_df,
    update_df,
    read_core_csv
    )
from crop.structure import (
    Sensor,
    Type,
    Location,
    Readings_Advantix
    )



def SQL_insert_data(db_name, csv_path):
    """
    Function description

    Args:
        pd_df - 

    Returns:
        success - status
        log - error message
    """

    error = False
    log = ""


    # Checks if db exists, if not creates it with tables. 
    error, log = create_database(SQL_CONNECTION_STRING, db_name)
    if error: return error, log
    
    # Creates an engine to connect to the db
    try: 
        engine = create_engine(SQL_CONNECTION_STRING + db_name)
    except:
        error = True
        log = "Error connecting to the database"
        return error, log
    
    # Populates db with core data (sensors, locations, sensor types)
    success, log, df = read_core_csv(csv_path)
    if not success: print (log)

    if df.empty != True:
        update_df (engine, df, Type)
        print (df)
        #bulk_insert_df(engine, df, Type)
    else: 
        error = True
        log = "dataframe empty"
        return error, log




    #Sensor_Types_data = load_data_pd(SENSOR_TYPES)
    #Locations = load_data_pd(LOCATIONS)


    # Populates with Advantix data 
    #ADVANTIX_DF= pd.read_csv(CWD+"\\data\\Advantix\\data-20190821-test1.csv")
    #bulk_insert_df(engine, ADVANTIX_DF, structure.Readings_Advantix)


#Insert sensortypes first. 
#SQL_insert_data(SQL_DBNAME, "%s\\%s" % (CONST_COREDATA_DIR, SENSOR_TYPE_CSV))
SQL_insert_data(SQL_DBNAME, "%s\\%s" % (CONST_COREDATA_DIR, SENSOR_TYPE_CSV))