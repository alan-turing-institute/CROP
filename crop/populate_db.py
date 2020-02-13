"""
Python module to perform data ingress operations

"""

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship


from crop.structure import (
    Sensor,
    Type,
    Location,
    Readings_Advantix
    )

from crop.db import (
    connect_db
)


def update_df (engine, Data, Class):
    """
    Bulk update data into the database. 
    Can update values based on id but cant insert new.
    """
    #Creates/Opens a new session (connection to the db)
    session = sessionmaker()
    #binds the engine to this session
    session.configure(bind=engine)
    s = session()

    #listentries
    #dict = Data.to_dict(orient="records")

        #entry = Class(type_id=5, sensor_type="hola", description = "sldkjfsldkj")
    #s.add(Class(type_id=5, sensor_type="hola", description = "sldkjfsldkj"))
    #s.add_all(Class(Data.to_dict(orient="records")))
    #s.bulk_update_mappings(Class, Data.to_dict(orient="records"))

    s.commit()
    s.close()
    return (Data)
 
def merge_df (engine, df, Class):
    """
    Bulk update data into the database. 
    Can update values based on id but cant insert new.
    """
    
    #Creates/Opens a new session (connection to the db)
    Session = sessionmaker()
    #binds the engine to this session
    Session.configure(bind=engine)
    session = Session()
    
    #TODO: TRY TO FIND A SOLUTION FOR UPDATING DATA
    #first option: bulk insert
    session.bulk_update_mappings(Type, df.to_dict(orient="records"))
    #second option insert by row. 
    #for i,row in df.iterrows():
        #pass
        #type = Type(type_id = row["type_id"], sensor_type = row["sensor_type"], description = row["description"])
        #session.add(type)
        

    session.commit()
    session.close()
    return True, df



#def SQL_insert_data(db_name, csv_path):
#    """
#    Function description

#    Args:
#        pd_df - 

#    Returns:
#        success - status
#        log - error message
#    """

#    error = False
#    log = ""


#    # Checks if db exists, if not creates it with tables. 
#    error, log = create_database(SQL_CONNECTION_STRING, db_name)
#    if error: return error, log
    
#    # Creates an engine to connect to the db
#    try: 
#        engine = create_engine(SQL_CONNECTION_STRING + db_name)
#    except:
#        error = True
#        log = "Error connecting to the database"
#        return error, log
    
#    # Populates db with core data (sensors, locations, sensor types)
#    success, log, df = read_core_csv(csv_path)
#    if not success: print (log)

#    if df.empty != True:
#        #update_df (engine, df, Type)
#        #print (df)
#        bulk_insert_df(engine, df, Type)
#        bulk_insert_df(engine, df, Type)
#    else: 
#        error = True
#        log = "dataframe empty"
#        return error, log




    #Sensor_Types_data = load_data_pd(SENSOR_TYPES)
    #Locations = load_data_pd(LOCATIONS)


    # Populates with Advantix data 
    #ADVANTIX_DF= pd.read_csv(CWD+"\\data\\Advantix\\data-20190821-test1.csv")
    #bulk_insert_df(engine, ADVANTIX_DF, structure.Readings_Advantix)


#Insert sensortypes first. 
#SQL_insert_data(SQL_DBNAME, "%s\\%s" % (CONST_COREDATA_DIR, SENSOR_TYPE_CSV))
#SQL_insert_data(SQL_DBNAME, "%s\\%s" % (CONST_COREDATA_DIR, SENSOR_TYPE_CSV))