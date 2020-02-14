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

from crop.constants import (
    CONST_ADVANTIX_COL_MODBUSID,
    CONST_ADVANTIX,
    ADVANTIX_READINGS_TABLE_NAME,
    CONST_ADVANTIX_COL_TIMESTAMP,
    CONST_ADVANTIX_COL_TEMPERATURE,
    CONST_ADVANTIX_COL_HUMIDITY,
    CONST_ADVANTIX_COL_CO2LEVEL
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
            try:
                entry_id = session.query(ADVANTIX_READINGS_TABLE_NAME).\
                                filter(Readings_Advantix.sensor_id == adv_sensor_id).\
                                filter(Readings_Advantix.Timestamp == adv_timestamp).\
                                first().id
            except:
                entry_id = -1

            if entry_id == -1:
                data = Readings_Advantix(
                    sensor_id=adv_sensor_id, 
                    Timestamp=adv_timestamp, 
                    Temperature=row[CONST_ADVANTIX_COL_TEMPERATURE], 
                    Humidity=row[CONST_ADVANTIX_COL_HUMIDITY], 
                    Co2=row[CONST_ADVANTIX_COL_CO2LEVEL])

                session.add(data)

            #else: Duplicate???
            
        # TODO: session commit 
           
    return result, log
