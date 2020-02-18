"""
Python module to perform data ingress operations

"""

from datetime import date
import datetime as dt
import pandas as pd
from sqlalchemy import create_engine, cast, DATE, DateTime
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

from crop.constants import (
    CONST_ADVANTIX_COL_MODBUSID,
    CONST_ADVANTIX,
    ADVANTIX_READINGS_TABLE_NAME,
    CONST_ADVANTIX_COL_TIMESTAMP,
    CONST_ADVANTIX_COL_TEMPERATURE,
    CONST_ADVANTIX_COL_HUMIDITY,
    CONST_ADVANTIX_COL_CO2LEVEL,
    CONST_ADVANTIX_TEST_10
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

    result = True
    log = ""
    cnt_dupl = 0
    
    try:
        adv_type_id = session.query(Type).filter(Type.sensor_type == CONST_ADVANTIX).first().type_id
    except:
        result = False
        log = "Sensor type {} was not found.".format(CONST_ADVANTIX)
        return result, log    

    for _, row in df.iterrows():
        
        adv_device_id = row[CONST_ADVANTIX_COL_MODBUSID]
        adv_timestamp = row[CONST_ADVANTIX_COL_TIMESTAMP]

        # Gets the id of the sensor with type=advantix and device_id=modbusid
        try:
            adv_sensor_id = session.query(Sensor).\
                            filter(Sensor.device_id == str(adv_device_id)).\
                            filter(Sensor.type_id == adv_type_id).\
                            first().sensor_id
        except:
            adv_sensor_id = -1
            result = False
            log = "{} sensor with {} = {} was not found.".format(CONST_ADVANTIX, CONST_ADVANTIX_COL_MODBUSID, str(adv_device_id))
            break

        if adv_sensor_id != -1:
            # check if data entry already exists

            #print ("Timestamp: ", adv_timestamp, type(dt.datetime.fromtimestamp(adv_timestamp.timestamp())))
            #print ("db daytime: ", Readings_Advantix.Timestamp)

            #year = dt.datetime.fromtimestamp(adv_timestamp.timestamp()).year
            #month = dt.datetime.fromtimestamp(adv_timestamp.timestamp()).month
            #day = dt.datetime.fromtimestamp(adv_timestamp.timestamp()).day
            #hour = dt.datetime.fromtimestamp(adv_timestamp.timestamp()).hour
            #minute = dt.datetime.fromtimestamp(adv_timestamp.timestamp()).minute
            #second = dt.datetime.fromtimestamp(adv_timestamp.timestamp()).second
            #micros = dt.datetime.fromtimestamp(adv_timestamp.timestamp()).microsecond 
            #print (adv_timestamp)

            #print(session.query(ADVANTIX_READINGS_TABLE_NAME).filter(cast(Readings_Advantix.Timestamp, DateTime) == dt.datetime(2019,8,21,6,44,1,659000)).all() )

            #2019-08-21 15:22:42.862000
            #2019-08-21 06:44:01.659000

            #print(dt.datetime.fromtimestamp(adv_timestamp.timestamp()))
            #print(session.query(ADVANTIX_READINGS_TABLE_NAME).filter(Readings_Advantix.time_stamp == dt.datetime.fromtimestamp(adv_timestamp.timestamp())).all())
            #print(session.query(ADVANTIX_READINGS_TABLE_NAME).filter(Readings_Advantix.time_stamp == adv_timestamp).all())
            #
            #try:
            #entry_id = 
            found = False
            try:
                query_result = session.query(ADVANTIX_READINGS_TABLE_NAME).\
                                filter(Readings_Advantix.sensor_id == adv_sensor_id).\
                                filter(Readings_Advantix.time_stamp == adv_timestamp).\
                                first()

                if query_result is not None:
                    found = True

            except:
                found = False

 
            if not found:
                data = Readings_Advantix(
                    sensor_id=adv_sensor_id, 
                    time_stamp=adv_timestamp, 
                    temperature=row[CONST_ADVANTIX_COL_TEMPERATURE], 
                    humidity=row[CONST_ADVANTIX_COL_HUMIDITY], 
                    co2=row[CONST_ADVANTIX_COL_CO2LEVEL])
                session.add(data)
 
            else: cnt_dupl += 1
        # TODO: session commit 
       
    if cnt_dupl != 0:
        result = False
        log = "Cannot insert {} duplicate values".format(cnt_dupl)

    return result, log