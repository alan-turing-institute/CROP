"""
Python module to import data using Openweatherdata API
"""

import logging
import time
from datetime import datetime
import requests
import pandas as pd

from .db import connect_db, session_open, session_close
from .structure import (
    ReadingsWeatherClass,
)
from .utils import log_upload_event
from .constants import (
    CONST_API_WEATHER_TYPE,
    CONST_OPENWEATHERMAP_APIKEY,
)
from .sensors import get_db_weather_data

# see https://openweathermap.org/api/one-call-3
lat = 51.45
lon = 0.14
units = "metric" # returns temperature in Celsius and wind speed in meter/sec
CONST_OPENWEATHERMAP_URL = f"https://api.openweathermap.org/data/3.0/onecall?"\
f"lat={lat}&lon={lon}&units={units}&appid="


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

    logging.info("new data with size len(new_data_df): {}\n\n".format(len(new_data_df)))
    if len(new_data_df) > 0:
        # this is the current time in seconds since epoch
        start_time: float = time.time()
        session = session_open(engine)
        for idx, row in new_data_df.iterrows():
            data = ReadingsWeatherClass(
                sensor_id=0,
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


def get_openweathermap_data(dt_to):
    """
    Retrieve hourly weather forecast for up to 48 hours from the openweathermap API.

    Parameters
    ----------
    dt_to: datetime, latest time for returned records.
    Requests beyond 48h into the future will return a maximum of 48h of forecast data.
    
    Returns
    -------
    success: bool, True if everything OK
    error: str, empty string if everything OK
    weather_df: pd.DataFrame, contains 1 row per hours data
    """
    url = CONST_OPENWEATHERMAP_URL
    url += CONST_OPENWEATHERMAP_APIKEY

    hourly_records = [] # list keeping track of records for all hours
    error = ""

    # do API call and get data in right format
    response = requests.get(url)

    # check for success of the request
    if response.status_code != 200:
        error = "Request's [%s] status code: %d" % (
            url[: min(70, len(url))],
            response.status_code,
        )
        sucess = False
        return sucess, error, None
    # keep only hourly data from the API response
    hourly_data = response.json()["hourly"]

    # loop through every hour in hourly data
    for hour in hourly_data:
        record = {} # dict keeping track of this hour's records
        record["timestamp"] = datetime.fromtimestamp(hour["dt"])
        record["temperature"] = hour["temp"] # returned in Celsius
        record["air_pressure"] = hour["pressure"] # sea level atmos pressure (hPa)
        record["relative_humidity"] = hour["humidity"] # (%)
        record["wind_speed"] = hour["wind_speed"] # (meter/sec)
        record["wind_direction"] = hour["wind_deg"] # (degrees)
        record["icon"] = hour["weather"][0]["icon"] # descriptive weather icon
        record["source"] = "openweatherdata"
        record["rain"] = 0.0
        # note rain data only returned where available
        if "rain" in hour.keys():
            record["rain"] += hour["rain"]["1h"]
        hourly_records.append(record)
    weather_df = pd.DataFrame(hourly_records) # create a pandas dataframe
    weather_df.set_index("timestamp", inplace=True) # set the index to become "timestamp" column
    df_index = weather_df.index # get the indices, i.e. all the timestamps in the dataframe
    timestamp_max = min(df_index, key=lambda x:abs(x-dt_to)) # find timestamp closest to requested end timestamp
    weather_df = weather_df[:timestamp_max] # crop the dataframe at that timestamp

    success = True
    log = "\nSuccess: Weather dataframe \n{}".format(weather_df)
    logging.info(log)
    return success, error, weather_df
