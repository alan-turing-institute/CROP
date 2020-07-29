"""
Python module to import data using 30 MHz API
"""

import logging
import time
from datetime import datetime, timedelta
import requests
import pandas as pd

from sqlalchemy import and_

from __app__.crop.db import connect_db, session_open, session_close
from __app__.crop.structure import (
    TypeClass,
    SensorClass,
    ReadingsZensieTRH,
)
from __app__.crop.utils import query_result_to_array
from __app__.crop.constants import (
    CONST_CROP_30MHZ_APIKEY,
    CONST_ZENSIE_TRH_SENSOR_TYPE,
)
from __app__.crop.ingress import log_upload_event
from __app__.crop.sensors import get_zensie_trh_sensor_data

CONST_CHECK_URL_PATH = "https://api.30mhz.com/api/stats/check"
CONST_CHECK_PARAMS = "statisticType=averages&intervalSize=5m"


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
        "Content-Type": "application/json",
        "Authorization": api_key,
    }

    dt_from_iso = dt_from.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    dt_to_iso = dt_to.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    url = "{}/{}/from/{}/until/{}?{}".format(
        CONST_CHECK_URL_PATH, check_id, dt_from_iso, dt_to_iso, CONST_CHECK_PARAMS
    )

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data_df = pd.read_json(response.content).T

        if data_df.empty:
            error = "Request [%s]: no data" % (url[: min(70, len(url))])
            success = False

    else:
        error = "Request's [%s] status code: %d" % (
            url[: min(70, len(url))],
            response.status_code,
        )
        success = False

    if success:
        data_df.reset_index(inplace=True, drop=False)
        data_df.rename(columns={"index": "Timestamp"}, inplace=True)

        for col_name in data_df.columns:

            if ".temperature" in col_name:
                data_df.rename(columns={col_name: "Temperature"}, inplace=True)

            elif ".humidity" in col_name:
                data_df.rename(columns={col_name: "Humidity"}, inplace=True)

        data_df.set_index("Timestamp", inplace=True)

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

    query = session.query(
        SensorClass.type_id, SensorClass.id, SensorClass.device_id,
    ).filter(
        and_(TypeClass.sensor_type == sensor_type, SensorClass.type_id == TypeClass.id,)
    )

    readings = session.execute(query).fetchall()

    result = query_result_to_array(readings, date_iso=False)

    return result


def import_zensie_trh_data(conn_string, database, dt_from, dt_to):
    """
    Uploads zensie temperature and relative humidity data to the CROP database.

    Arguments:
        conn_string: connection string
        database: the name of the database
        dt_from: date range from
        dt_to: date range to
    Returns:
        status, error
    """

    log = ""
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
        return log_upload_event(
            CONST_ZENSIE_TRH_SENSOR_TYPE, "Zensie API", success, log, conn_string
        )

    for zensie_sensor_i, zensie_sensor in enumerate(zensie_sensor_list):

        sensor_id = zensie_sensor["sensors_id"]
        sensor_check_id = zensie_sensor["sensors_device_id"]

        logging.debug(
            "sensor_id: {} | sensor_check_id: {}".format(sensor_id, sensor_check_id)
        )

        if sensor_id > 0 and len(sensor_check_id) > 0:

            logging.debug(
                "sensor_id: {} | dt_from: {}, dt_to: {}".format(
                    sensor_id, dt_from, dt_to
                )
            )

            # Sensor data from Zensie
            sensor_success, sensor_error, api_data_df = get_api_sensor_data(
                CONST_CROP_30MHZ_APIKEY, sensor_check_id, dt_from, dt_to
            )

            logging.debug(
                "sensor_id: {} | sensor_success: {}, sensor_error: {}".format(
                    sensor_id, sensor_success, sensor_error
                )
            )

            if sensor_success:
                # Sensor data from database
                session = session_open(engine)
                db_data_df = get_zensie_trh_sensor_data(
                    session,
                    sensor_id,
                    dt_from + timedelta(hours=-1),
                    dt_to + timedelta(hours=1),
                )
                session_close(session)

                if len(db_data_df) > 0:
                    # Filtering only new data
                    new_data_df = api_data_df[~api_data_df.index.isin(db_data_df.index)]

                    logging.debug(
                        "sensor_id: {} | len(db_data_df): {}".format(
                            sensor_id, len(db_data_df)
                        )
                    )
                else:
                    new_data_df = api_data_df

                logging.debug(
                    "sensor_id: {} | len(new_data_df): {}".format(
                        sensor_id, len(new_data_df)
                    )
                )

                if len(new_data_df) > 0:

                    start_time = time.time()

                    session = session_open(engine)
                    for idx, row in new_data_df.iterrows():

                        data = ReadingsZensieTRH(
                            sensor_id=sensor_id,
                            timestamp=idx,
                            temperature=row["Temperature"],
                            humidity=row["Humidity"],
                        )

                        session.add(data)
                    
                    session.query(SensorClass).\
                        filter(SensorClass.id == sensor_id).\
                        update({"last_updated": datetime.now()})

                    session_close(session)

                    elapsed_time = time.time() - start_time

                    logging.debug(
                        "sensor_id: {} | elapsed time importing data: {} s.".format(
                            sensor_id, elapsed_time
                        )
                    )

                    upload_log = "New: {} (uploaded);".format(len(new_data_df.index))
                    log_upload_event(
                        CONST_ZENSIE_TRH_SENSOR_TYPE,
                        "Zensie API; Sensor ID {}".format(sensor_id),
                        sensor_success,
                        upload_log,
                        conn_string,
                    )

            else:
                log_upload_event(
                    CONST_ZENSIE_TRH_SENSOR_TYPE,
                    "Zensie API; Sensor ID {}".format(sensor_id),
                    sensor_success,
                    sensor_error,
                    conn_string,
                )

    return True, None


def import_zensie_data():
    """
    Imports all zensie data

    """

    from __app__.crop.constants import SQL_CONNECTION_STRING, SQL_DBNAME

    # date_ranges = pd.date_range(start='2020-01-01', end='2020-08-01', periods=20)

    # for date_idx, dt_to in enumerate(date_ranges):

    #     if date_idx != 0:
    #         import_zensie_trh_data(SQL_CONNECTION_STRING, SQL_DBNAME, dt_from, dt_to)

    #     dt_from = dt_to

    dt_to = datetime.now()
    dt_from = dt_to + timedelta(days=-10)
    
    import_zensie_trh_data(SQL_CONNECTION_STRING, SQL_DBNAME, dt_from, dt_to)


# if __name__ == "__main__":

#     import_zensie_data()
