"""
Importing zensie data using Azure FunctionApp.
"""


import datetime
import logging

import azure.functions as func

def stark_import(mytimer: func.TimerRequest):
    """
    The main STARK import Azure Function routine.

    """

    utc_timestamp = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )

    logging.info("Python zensie timer trigger function started at %s", utc_timestamp)

    
 
    utc_timestamp = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )

    logging.info("Python zensie timer trigger function finished at %s", utc_timestamp)
