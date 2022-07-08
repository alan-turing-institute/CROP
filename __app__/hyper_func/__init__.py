"""
Importing Hyper.ag data using Azure FunctionApp.
"""

from datetime import datetime, timedelta, timezone
import logging

import azure.functions as func

from __app__.crop.ingress_hyper import import_hyper_data
from __app__.crop.constants import SQL_CONNECTION_STRING, SQL_DBNAME


def hyper_import(mytimer: func.TimerRequest):
    """
    The main Hyper import Azure Function routine.
    """

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    logging.info("Python Hyper timer trigger function started at %s", utc_timestamp)

    dt_to = datetime.now()
    dt_from = dt_to + timedelta(days=-1)
    import_hyper_data(SQL_CONNECTION_STRING, SQL_DBNAME, dt_from, dt_to)

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    logging.info("Python Hyper timer trigger function finished at %s", utc_timestamp)
