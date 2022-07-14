"""
Python module to import data using the Hyper.ag API
"""

from collections.abc import Iterable
import logging
import time
from datetime import datetime, timedelta
import requests
import pandas as pd

from sqlalchemy import and_
from sqlalchemy.exc import ProgrammingError

from __app__.crop.db import connect_db, session_open, session_close
from __app__.crop.structure import (
    TypeClass,
    SensorClass,
    ReadingsAranetTRHClass,
)
from __app__.crop.utils import query_result_to_array
from __app__.crop.constants import CONST_CROP_HYPER_APIKEY, CONST_ARANET_TRH_SENSOR_TYPE

from __app__.crop.ingress import log_upload_event
from __app__.crop.sensors import get_sensor_readings_db_timestamps


CONST_CHECK_URL_PATH = "https://zcf.hyper.ag/api/sites/1/analytics/v3/device_metrics"


def get_api_sensor_data(api_key, dt_from, dt_to):
    """
    Makes a request to download sensor data for a specified period of time.
    Note that unlike the equivalent Zensie function, this gets data for _all_ sensors,
    and returns it as a dict, keyed by Aranet id.

    Arguments:
        api_key: api key for authentication
        dt_from: date range from
        dt_to: date range to
    Return:
        success: whether data request was succesful
        error: error message
        data_df_dict: dictionary of {aranet_pro_id (str): DataFrame of sensor_data}
    """

    success = True
    error = ""
    data_df_dict = {}

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    }

    dt_from_iso = dt_from.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    dt_to_iso = dt_to.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    url = CONST_CHECK_URL_PATH

    params = {
        "start_time": dt_from_iso,
        "end_time": dt_to_iso,
        "metrics": "aranet_ambient_temperature,aranet_relative_humidity",
        "resolution": "10m",
        "metadata": "true",
    }
    response = requests.get(url, headers=headers, params=params, verify=False)

    if response.status_code != 200:
        error = "Request's [%s] status code: %d" % (url[:70], response.status_code)
        success = False
        return success, error, data_df_dict
    # if we got to here, we have an API response for all T/RH sensors
    data = response.json()
    # the metadata contains a mapping between the Hyper id (MAC address) and the
    # aranet_pro_id
    device_mapping = data["metadata"]["devices"]
    timestamps = data["labels"]
    value_dicts = data["series"]

    for value_dict in value_dicts:
        hyper_id = value_dict["device_id"]
        aranet_pro_id = device_mapping[hyper_id]["vendor_device_id"]

        metric_name = value_dict["metric"]
        if metric_name == "aranet_ambient_temperature":
            metric_name = "Temperature"
        elif metric_name == "aranet_relative_humidity":
            metric_name = "Humidity"

        if aranet_pro_id not in data_df_dict:
            data_df = pd.DataFrame({"Timestamp": pd.to_datetime(timestamps)})
            data_df.set_index("Timestamp", inplace=True)
            data_df_dict[aranet_pro_id] = data_df
        else:
            data_df = data_df_dict[aranet_pro_id]
        data_df[metric_name] = value_dict["values"]
        # put this DataFrame into a dict, keyed by the aranet id
        data_df_dict[aranet_pro_id] = data_df

    return success, error, data_df_dict


def _get_sensor_id(aranet_pro_id, engine):
    """Get the CROP sensor ID, from the CROP database, based on the Aranet Pro ID."""
    session = session_open(engine)
    query = session.query(
        SensorClass.id,
    ).filter(SensorClass.aranet_pro_id == aranet_pro_id)
    sensor_id = session.execute(query).fetchone()
    if isinstance(sensor_id, Iterable):
        sensor_id = sensor_id[0]
    session_close(session)
    return sensor_id


def import_hyper_data(conn_string, database, dt_from, dt_to):
    """
    Uploads temperature and relative humidity data to the CROP database.

    Arguments:
        conn_string: connection string
        database: the name of the database
        dt_from: date range from
        dt_to: date range to
    Returns:
        status, error
    """
    # Create a CROP database connection to use.
    success, log, engine = connect_db(conn_string, database)
    if not success:
        logging.info(log)
        return success, log

    # Create the readings table if it doesn't exist.
    try:
        ReadingsAranetTRHClass.__table__.create(bind=engine)
    except ProgrammingError:
        # The table already exists.
        pass

    logging.info(f"Requesting data from {dt_from} to {dt_to} from the Hyper API")
    success, error, hyper_data_dict = get_api_sensor_data(
        CONST_CROP_HYPER_APIKEY, dt_from, dt_to
    )
    if not success:
        logging.info(error)
        return success, error

    # Write the data to the CROP database, sensor by sensor.
    for aranet_pro_id, api_data_df in hyper_data_dict.items():
        logging.info(f"Writing data for sensor with Aranet Pro ID {aranet_pro_id}")
        # Find the sensor_id that CROP uses for this sensor, and fetch existing data for
        # this sensor.
        sensor_id = _get_sensor_id(aranet_pro_id, engine)
        if sensor_id is None:
            logging.info(f"Sensor {aranet_pro_id} does not exist in the CROP database")
            continue

        session = session_open(engine)
        db_data_df = get_sensor_readings_db_timestamps(
            session,
            sensor_id,
            dt_from + timedelta(hours=-1),
            dt_to + timedelta(hours=1),
        )
        session_close(session)

        # From the data returned by Hyper, filter out all the data we already have.
        if len(db_data_df) > 0:
            api_index = api_data_df.index
            db_index = db_data_df.index.tz_localize(api_index.tz)
            new_data_df = api_data_df[~api_index.isin(db_index)]
        else:
            new_data_df = api_data_df
        new_data_df = new_data_df[~new_data_df.isna().any(axis=1)]
        if len(new_data_df) == 0:
            continue

        logging.info(f"Writing {len(new_data_df)} new readings")
        session = session_open(engine)
        for idx, row in new_data_df.iterrows():
            data = ReadingsAranetTRHClass(
                sensor_id=sensor_id,
                timestamp=idx,
                temperature=row["Temperature"],
                humidity=row["Humidity"],
            )
            session.add(data)
        session.query(SensorClass).filter(SensorClass.id == sensor_id).update(
            {"last_updated": datetime.utcnow()}
        )
        session_close(session)

        upload_log = "New: {} (uploaded);".format(len(new_data_df.index))
        log_upload_event(
            CONST_ARANET_TRH_SENSOR_TYPE,
            "Hyper API; Sensor ID {}".format(sensor_id),
            success,
            upload_log,
            conn_string,
        )

    return True, None
