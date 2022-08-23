"""
Importing GrowApp data using Azure FunctionApp.
"""

from datetime import datetime, timedelta, timezone
import logging

import azure.functions as func

from core.ingress_growapp import import_growapp_data
from core.constants import SQL_CONNECTION_STRING, SQL_DBNAME


def growapp_import(mytimer: func.TimerRequest):
    """
    The main GrowApp import Azure Function routine.
    """

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    logging.info("Python GrowApp timer trigger function started at %s", utc_timestamp)

    dt_to = datetime.utcnow()
    dt_from = dt_to + timedelta(days=-1)
    import_growapp_data(dt_from, dt_to)

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    logging.info("Python GrowApp timer trigger function finished at %s", utc_timestamp)
