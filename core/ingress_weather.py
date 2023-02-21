"""
Python module to import data using Openweatherdata API
"""

import logging
import time
from datetime import datetime, timedelta
import requests
import pandas as pd

from sqlalchemy import and_

from .db import connect_db, session_open, session_close
from .structure import (
    ReadingsWeatherClass,
    SensorClass,
)
from .utils import query_result_to_array, log_upload_event
from .constants import (
    CONST_API_WEATHER_TYPE,
    CONST_OPENWEATHERMAP_APIKEY,
    CONST_OPENWEATHERMAP_HISTORICAL_URL,
)
from .sensors import get_db_weather_data


def get_openweathermap_sensor_id(session):
    query = session.query(SensorClass.id).filter(SensorClass.name == "OpenWeatherMap")
    sensor_id = session.execute(query).fetchone()[0]
    return sensor_id


def upload_openweathermap_data(
    conn_string: str, database: str, dt_from: datetime, dt_to: datetime
):
    """
    Uploads openweathermap data to the CROP database.

    Arguments:
        conn_string: connection string
        database: the name of the database
        dt_from: date range from
        dt_to: date range to
    Returns:
        status, error
    """
    # connect to the DB to get weather data already there, so we don't duplicate
    success, log, engine = connect_db(conn_string, database)
    if not success:
        logging.error(log)
        return success, log
    session = session_open(engine)
    df_db = get_db_weather_data(session, dt_from, dt_to)

    # now get the Openweathermap API data
    success, error, df_api = get_openweathermap_data(dt_from, dt_to)
    if not success:
        return success, error

    # filter out the rows that are already in the db data
    new_data_df = df_api[~df_api.index.isin(df_db.index)]

    sensor_id = get_openweathermap_sensor_id(session)
    logging.info("new data with size len(new_data_df): {}\n\n".format(len(new_data_df)))
    if len(new_data_df) > 0:
        # this is the current time in seconds since epoch
        start_time: float = time.time()
        session = session_open(engine)
        for idx, row in new_data_df.iterrows():
            data = ReadingsWeatherClass(
                sensor_id=sensor_id,
                timestamp=idx,
                temperature=row["temperature"],
                rain_probability=None,  # not in openweathermap data
                rain=row["rain"],
                relative_humidity=row["relative_humidity"],
                wind_speed=row["wind_speed"],
                wind_direction=row["wind_direction"],
                air_pressure=row["air_pressure"],
                radiation=None,  # not in openweathermap data
                icon=row["icon"],
                source=row["source"],
            )
            session.add(data)
        session_close(session)

        elapsed_time = time.time() - start_time

        logging.debug(
            "openweathermap | elapsed time importing data: {} s.".format(elapsed_time)
        )

        upload_log = "New: {} (uploaded);".format(len(new_data_df.index))
        log_upload_event(
            CONST_API_WEATHER_TYPE,
            "Openweathermap API",
            success,
            upload_log,
            conn_string,
        )

    else:
        log_upload_event(
            CONST_API_WEATHER_TYPE,
            "Openweathermap API",
            success,
            error,
            conn_string,
        )
    return True, None


def get_openweathermap_data(dt_from, dt_to):
    """
    Retrieve weather data from the openweathermap API.
    Note that each API call returns the hourly data from 00:00 to 23:59 on
    the date specified by the 'dt' timestamp, so we need to make 2 calls
    in order to get the full set of data for the last 24 hours.

    Parameters
    ----------
    dt_from: datetime, earliest time for returned records
    dt_to: datetime, latest time for returned records

    Returns
    -------
    success: bool, True if everything OK
    error: str, empty string if everything OK
    df: pd.DataFrame, contains 1 row per hours data.
    """
    base_url = CONST_OPENWEATHERMAP_HISTORICAL_URL
    base_url += CONST_OPENWEATHERMAP_APIKEY
    # get unix timestamps for start and end times
    timestamp_from = int(dt_from.timestamp())
    timestamp_to = int(dt_to.timestamp())
    hourly_records = []
    error = ""
    # do API call and get data in right format for both dates.
    for ts in [timestamp_from, timestamp_to]:
        url = base_url + "&dt={}".format(ts)
        response = requests.get(url)

        if response.status_code != 200:
            error = "Request's [%s] status code: %d" % (
                url[: min(70, len(url))],
                response.status_code,
            )
            success = False
            return success, error, None
        hourly_data = response.json()["hourly"]

        for hour in hourly_data:
            if hour["dt"] < timestamp_from or hour["dt"] > timestamp_to:
                continue
            record = {}
            record["timestamp"] = datetime.fromtimestamp(hour["dt"])
            record["temperature"] = hour["temp"]
            record["air_pressure"] = hour["pressure"]
            record["relative_humidity"] = hour["humidity"]
            record["wind_speed"] = hour["wind_speed"]
            record["wind_direction"] = hour["wind_deg"]
            record["icon"] = hour["weather"][0]["icon"]
            record["source"] = "openweatherdata"
            record["rain"] = 0.0
            if "rain" in hour.keys():
                record["rain"] += hour["rain"]["1h"]
            hourly_records.append(record)
    weather_df = pd.DataFrame(hourly_records)
    weather_df.set_index("timestamp", inplace=True)
    success = True
    log = "\nSuccess: Weather dataframe \n{}".format(weather_df)
    logging.info(log)
    return success, error, weather_df
