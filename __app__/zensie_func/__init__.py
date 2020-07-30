"""
Importing zensie data using Azure FunctionApp.
"""

from datetime import datetime, timedelta, timezone
import logging

import azure.functions as func

from __app__.crop.ingress_zensie import import_zensie_trh_data
from __app__.crop.constants import SQL_CONNECTION_STRING, SQL_DBNAME

def zensie_import(mytimer: func.TimerRequest):
    """
    The main Zensie import Azure Function routine.

    """

    utc_timestamp = (
        datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    )

    logging.info("Python zensie timer trigger function started at %s", utc_timestamp)

    dt_to = datetime.now()
    dt_from = dt_to + timedelta(days=-1)
    
    logging.info("SQL_CONNECTION_STRING %s" % (SQL_CONNECTION_STRING))
    logging.info("SQL_DBNAME %s" % (SQL_DBNAME))

    import_zensie_trh_data(SQL_CONNECTION_STRING, SQL_DBNAME, dt_from, dt_to)
 
    utc_timestamp = (
        datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    )

    logging.info("Python zensie timer trigger function finished at %s", utc_timestamp)
