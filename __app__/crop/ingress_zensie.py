"""
Python module to import data using 30 MHz API
"""

import os
import requests
import json
import pandas as pd

from sqlalchemy import and_

from __app__.crop.db import connect_db, session_open, session_close
from __app__.crop.structure import (
    TypeClass,
    SensorClass,
)
from __app__.crop.utils import query_result_to_array

from __app__.crop.constants import (
    CONST_CROP_30MHZ_APIKEY,
    CONST_ZENSIE_TRH_SENSOR_TYPE,
)

from __app__.crop.ingress import log_upload_event

CONST_CHECK_URL_PATH = 'https://api.30mhz.com/api/stats/check'
CONST_CHECK_PARAMS = 'statisticType=averages&intervalSize=5m'


def get_api_sensor_data(api_key, check_id, dt_from, dt_to):
    """
    Makes a request to download sensor data for a specified period of time.

    Arguments:
        api_key: api key for authetication
        check_id: sensor identifier 
        dt_from: date range from
        dt_to: date range to
    Return:
        success: whether data request was succesful
        error: error message
        data_df: sensor data as pandas dataframe
    """

    success = True
    error = ""
    data_df = None

    headers = {
        'Content-Type': 'application/json',
        'Authorization': api_key,
    }

    dt_from_iso = dt_from.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    dt_to_iso = dt_to.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    
    url = '{}/{}/from/{}/until/{}?{}'.format(CONST_CHECK_URL_PATH, check_id, dt_from_iso, dt_to_iso, CONST_CHECK_PARAMS)

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data_df = pd.read_json(response.content).T

        if data_df.empty:
            error = "Request [%s]: no data" % (url)
            success = False

    else:
        error = "Request's [%s] status code: %d" % (url, response.status_code)
        success = False
    
    if success:
        data_df.reset_index(inplace=True, drop=False)
        data_df.rename(columns={'index': 'Timestamp'}, inplace=True)

        for col_name in data_df.columns:

            if ".temperature" in col_name:
                data_df.rename(columns={col_name: 'Temperature'}, inplace=True)

            elif ".humidity" in col_name:
                data_df.rename(columns={col_name: 'Humidity'}, inplace=True)

    return success, error, data_df


def get_zensie_sensors_list(session, sensor_type):
    """
    Makes a list of ensie rth sensors with their check_id and ids.

    Arguments:
        session: sql session
        sensor_type: zensie sensor type
    Returns:
        result: a list of zensie rth sensors with their check_id and ids.
    """

    query = (
        session.query(
            SensorClass.type_id,
            SensorClass.id,
            SensorClass.device_id,
        )
        .filter(
            and_(
                TypeClass.sensor_type == sensor_type,
                SensorClass.type_id == TypeClass.id,
            )
        )
    )

    readings = session.execute(query).fetchall()

    result = query_result_to_array(readings, date_iso=False)

    return result


def import_zensie_trh_data(conn_string, database):
    """
    Uploads zensie temperature and relative humidity data to the CROP database.

    Arguments:
        conn_string: connection string
        database: the name of the database
    Returns:
        status, error
    """

    sensor_type = CONST_ZENSIE_TRH_SENSOR_TYPE

    success, log, engine = connect_db(conn_string, database)

    if not success:
        return success, log

    # get the list of zensie trh sensors
    try:
        session = session_open(engine)
        zensie_sensor_list = get_zensie_sensors_list(session, sensor_type)
        session_close(session)

        if zensie_sensor_list is None or len(zensie_sensor_list) == 0:
            success = False
            log = "No sensors with sensor type {} were found.".format(sensor_type)

    except:
        session_close(session)
        success = False
        log = "No sensors with sensor type {} were found.".format(sensor_type)

    if not success:
        return log_upload_event(CONST_ZENSIE_TRH_SENSOR_TYPE, "Zensie API", success, log, conn_string)


    print(zensie_sensor_list)


if __name__ == "__main__":

    from __app__.crop.constants import  SQL_CONNECTION_STRING, SQL_DBNAME

    conn_string = SQL_CONNECTION_STRING
    database = SQL_DBNAME

    import_zensie_trh_data(conn_string, database)
