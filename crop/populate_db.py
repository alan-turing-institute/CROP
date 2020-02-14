"""
Python module to perform data ingress operations

"""

import datetime as dt
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

def session_open(engine):
    """
    Opens a new connection/session to the db and binds the engine
    -engine: the connected engine
    """
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    return session

def session_close(session):
    """
    Closes the current open session
    -session: an open session
    """
    session.commit()
    session.close()

def insert_advantix_data(session, df):
    """
    The function will take the prepared advantix data frame from the ingress module
    and find sensor id with respect to modbusid and sensor type and insert data into the db.
    -engine: the db engine
    -type_df: dataframe containing the type values
    """

    log = ""
    last_timestamp_entry = session.query(Readings_Advantix).first().Timestamp

#    if df.empty != True:
#        #update_df (engine, df, Type)
#        #print (df)
#        bulk_insert_df(engine, df, Type)
#        bulk_insert_df(engine, df, Type)
#    else:
#        error = True
#        log = "dataframe empty"
#        return error, log

    for _, row in df.iterrows():
        # Checks the last's entry timestamp and checks if exists in the current df
        #if it already exists it passes
        if not last_timestamp_entry == pd.to_datetime(row['Timestamp']):

            #Checks if the type id is advantix and gets its type_id
            advantix_type_id = session.query(Type).filter(Type.sensor_type == 'Advantix').first().type_id
            device_id = row["Modbus ID"]

            #Gets the id of the sensor with type=advantix and device_id=modbusid
            sensorx_id = session.query(Sensor).filter(Sensor.device_id == str(device_id)).first().sensor_id

            #Prepares the data and adds them in the database
            data = Readings_Advantix(sensor_id=sensorx_id, Timestamp=row["Timestamp"], Temperature=row["Temperature"], Humidity=row["Humidity"], Co2=row["CO2 Level"])
            session.add(data)
        else: pass
    return True, log

def insert_type_data(session, type_df):
    """
    Insert test Type data into the database.
    -engine: the db engine
    -type_df: dataframe containing the type values
    """

    for _, row in type_df.iterrows():

        #Queries db and returns false if doesnt exist
        exists = session.query(Type).filter(Type.type_id == row['type_id']).scalar()

        if not exists:
            type = Type(type_id=row["type_id"], sensor_type=row["sensor_type"], description=row["description"])
            session.add(type)
        else: pass
    return True

def insert_sensor_data (session, sensor_df):
    """
    Insert test Sensor data into the database.
    -engine: the db engine
    -df: dataframe containing the sensor values
    """
   
    #Populates with type data
    for _, row in sensor_df.iterrows():
        #queries db and returns false if doesnt exist
        print (row)
        exists = session.query(Sensor).filter(Sensor.sensor_id == row['sensor_id']).scalar()
        if not exists:
            sensor = Sensor(sensor_id=row["sensor_id"], type_id=row["type_id"], device_id=row["device_id"], installation_date=row ["installation_date"])
            session.add(sensor)
        else: pass
    return True
W
def insert_location_data (session, location_df):
    """
    Insert test location data into the database.
    -session: the db engine
    -location_df: dataframe containing the sensor values
    """

    for _, row in location_df.iterrows():
        #queries db and returns false if doesnt exist
        exists = session.query(Location).filter(Location.sensor_id == row['sensor_id']).scalar()
        if not exists:
            locations = Location(sensor_id=row["sensor_id"], section=row["section"], column=row["column"], shelf=row ["shelf"])
            session.add(locations)
        else: pass
    return True
