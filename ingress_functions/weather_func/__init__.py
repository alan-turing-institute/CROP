"""
Importing weather data using Azure FunctionApp.
"""

from datetime import datetime, timedelta, timezone
import logging

import azure.functions as func

from __app__.crop.ingress_weather import upload_openweathermap_data
from __app__.crop.constants import SQL_CONNECTION_STRING, SQL_DBNAME


def weather_import(mytimer: func.TimerRequest):
    """
    The main weather import Azure Function routine.

    """

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    logging.info("Python weather timer trigger function started at %s", utc_timestamp)

    dt_to = datetime.utcnow()
    dt_from = dt_to + timedelta(days=-1)

    upload_openweathermap_data(SQL_CONNECTION_STRING, SQL_DBNAME, dt_from, dt_to)

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    logging.info("Python weather timer trigger function finished at %s", utc_timestamp)
