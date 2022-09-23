"""
Importing weather forecast data using Azure FunctionApp.
"""

from datetime import datetime, timedelta, timezone
import logging

import azure.functions as func

from core.ingress_weather_forecast import upload_openweathermap_data
from core.constants import SQL_CONNECTION_STRING, SQL_DBNAME


def weather_import(mytimer: func.TimerRequest):
    """
    The main weather forecast import Azure Function routine.

    """

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    logging.info("Python weather forecast timer trigger function started at %s", utc_timestamp)

    dt_to = datetime.utcnow() + timedelta(days=2)

    upload_openweathermap_data(SQL_CONNECTION_STRING, SQL_DBNAME, dt_to)

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    logging.info("Python weather forecast timer trigger function finished at %s", utc_timestamp)
