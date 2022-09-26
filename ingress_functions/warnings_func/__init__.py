"""
Create warnings in the database.
"""
from datetime import datetime, timedelta, timezone
import logging

import azure.functions as func

from core.warnings import create_and_upload_warnings


def create_warnings(mytimer: func.TimerRequest):
    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    logging.info("Python warnings timer trigger function started at %s", utc_timestamp)

    create_and_upload_warnings()

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    logging.info("Python warnings timer trigger function finished at %s", utc_timestamp)
