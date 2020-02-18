"""
Python module to populate a PostGres database with the
Advantix sensor data

"""

from sqlalchemy.orm import sessionmaker

from crop.structure import (
    Sensor,
    Type,
    Readings_Advantix
)


from crop.constants import (
    CONST_ADVANTIX_COL_MODBUSID,
    CONST_ADVANTIX,
    ADVANTIX_READINGS_TABLE_NAME,
    CONST_ADVANTIX_COL_TIMESTAMP,
    CONST_ADVANTIX_COL_TEMPERATURE,
    CONST_ADVANTIX_COL_HUMIDITY,
    CONST_ADVANTIX_COL_CO2LEVEL,
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

def insert_advantix_data(session, adv_df):
    """
    The function will take the prepared advantix data frame from the ingress module
    and find sensor id with respect to modbusid and sensor type and insert data into the db.
    -session: an open sqlalchemy session
    -adv_df: dataframe containing a checked advantix df
    -cnt_dupl: counts duplicate values
    """

    result = True
    log = ""
    cnt_dupl = 0

    # Gets the the assigned int id of the "Advantix" type
    try:
        adv_type_id = session.query(Type).filter(Type.sensor_type == CONST_ADVANTIX).first().type_id
    except:
        result = False
        log = "Sensor type {} was not found.".format(CONST_ADVANTIX)
        return result, log

    # Gets the sensor_id of the sensor with type=advantix and device_id=modbusid
    for _, row in adv_df.iterrows():

        adv_device_id = row[CONST_ADVANTIX_COL_MODBUSID]
        adv_timestamp = row[CONST_ADVANTIX_COL_TIMESTAMP]

        try:
            adv_sensor_id = session.query(Sensor).\
                            filter(Sensor.device_id == str(adv_device_id)).\
                            filter(Sensor.type_id == adv_type_id).\
                            first().sensor_id
        except:
            adv_sensor_id = -1
            result = False
            log = "{} sensor with {} = {} was not found.".format(
                CONST_ADVANTIX, CONST_ADVANTIX_COL_MODBUSID, str(adv_device_id))
            break

        # check if data entry already exists
        if adv_sensor_id != -1:
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

    if cnt_dupl != 0:
        result = False
        log = "Cannot insert {} duplicate values".format(cnt_dupl)

    return result, log
