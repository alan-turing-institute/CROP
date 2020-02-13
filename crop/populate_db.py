"""
Python module to perform data ingress operations

"""

import pandas as pd
import datetime as dt
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

def session_open (engine):
    
    #Creates/Opens a new connection to the db and binds the engine
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    return session

def session_close (session):
    session.commit()
    session.close()

def insert_advantix_data(session, df):
    """
    Insert data into the database. 
    -engine: the db engine
    -type_df: dataframe containing the type values
    """

    #Populates with type data
    last_timestamp_entry = session.query(Readings_Advantix).first().Timestamp
    for _,row in df.iterrows():
        #queries db and returns false if doesnt exist
        # get sensor id from type and modbusid.
        #print (row['Timestamp'], " ", pd.to_datetime(row['Timestamp']))
        if not last_timestamp_entry == pd.to_datetime(row['Timestamp']):
            advantix_type_id = session.query(Type).filter(Type.sensor_type=='Advantix').first().type_id
            #print (advantix_type_id)
            device_id = row["Modbus ID"]
            sensorx_id = session.query(Sensor).filter(Sensor.device_id == str(device_id)).first().sensor_id
            data = Readings_Advantix(sensor_id = sensorx_id, Timestamp = row["Timestamp"], Temperature = row["Temperature"], Humidity = row["Humidity"], Co2 = row["CO2 Level"])
            session.add(data)
        else: pass
    return True

def insert_type_data(session, type_df):
    """
    Insert data into the database. 
    -engine: the db engine
    -type_df: dataframe containing the type values
    """

    #Populates with type data
    for _,row in type_df.iterrows():
        #queries db and returns false if doesnt exist
        exists = session.query(Type).filter(Type.type_id==row['type_id']).scalar()
        if not exists:
            type = Type(type_id = row["type_id"], sensor_type = row["sensor_type"], description = row["description"])
            session.add(type)
        else: pass
    return True

def insert_sensor_data (session, sensor_df):
    """
    Insert data into the database. 
    -engine: the db engine
    -df: dataframe containing the sensor values
    """
   
    #Populates with type data
    for _,row in sensor_df.iterrows():
        #queries db and returns false if doesnt exist
        print (row)
        exists = session.query(Sensor).filter(Sensor.sensor_id==row['sensor_id']).scalar()
        if not exists:
            sensor = Sensor(sensor_id = row["sensor_id"], type_id = row["type_id"], device_id = row["device_id"], installation_date = row ["installation_date"])
            session.add(sensor)
        else: pass
    return True

def insert_location_data (session, location_df):
    """
    Insert data into the database. 
    -session: the db engine
    -location_df: dataframe containing the sensor values
    """
   
    #Populates with type data
    for _,row in location_df.iterrows():
        #queries db and returns false if doesnt exist
        print (row)
        exists = session.query(Location).filter(Location.sensor_id==row['sensor_id']).scalar()
        if not exists:
            locations = Location(sensor_id = row["sensor_id"], section = row["section"], column = row["column"], shelf = row ["shelf"])
            session.add(locations)
        else: pass
    return True




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