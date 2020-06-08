"""
Importing stark energy data using Azure FunctionApp.
"""


import datetime
import logging

import azure.functions as func

from __app__.crop.ingress import log_upload_event
from __app__.crop.ingress_energy import scrape_data, import_energy_data
from __app__.crop.constants import CONST_STARK, SQL_CONNECTION_STRING, SQL_DBNAME


def stark_import(mytimer: func.TimerRequest):
    """
    The main STARK import Azure Function routine.

    """

    utc_timestamp = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )

    logging.info("Python stark timer trigger function started at %s", utc_timestamp)

    # Get the data from the website
    status, error, energy_df = scrape_data()

    if not status:
        log_upload_event(
            CONST_STARK, "stark.co.uk", status, error, SQL_CONNECTION_STRING
        )
    else:
        status, error = import_energy_data(energy_df, SQL_CONNECTION_STRING, SQL_DBNAME)

    logging.info(f"Log: {status} {error}")

    utc_timestamp = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )

    logging.info("Python stark timer trigger function finished at %s", utc_timestamp)
