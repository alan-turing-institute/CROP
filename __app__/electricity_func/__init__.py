"""
Importing weather data using Azure FunctionApp.
"""

from datetime import datetime, timedelta, timezone
import logging

import azure.functions as func


from __app__.crop.ingress_energy_utc import import_stark_energy_data
from __app__.crop.constants import SQL_CONNECTION_STRING, SQL_DBNAME

def energy_import(mytimer: func.TimerRequest):
    """
    The main Zensie import Azure Function routine.

    """

    utc_timestamp = (
        datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    )

    logging.info("Python electricity consumption timer trigger function started at %s", utc_timestamp)
    
    import_stark_energy_data(SQL_CONNECTION_STRING, SQL_DBNAME)
 
    utc_timestamp = (
        datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    )

    logging.info("Python electricity consumption timer trigger function finished at %s", utc_timestamp)
