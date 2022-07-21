"""
Python module to read from the PurpleCrane GrowApp database, and write to CROP database
"""
import logging
import time
from datetime import datetime, timedelta
import requests
import pandas as pd
from urllib import parse

from sqlalchemy import and_
from sqlalchemy.exc import ProgrammingError

from __app__.crop.db import connect_db, session_open, session_close
from __app__.crop.structure import (
    LocationClass,
    CropTypeClass,
    BatchClass,
    BatchEventClass,
    HarvestClass,
)

from __app__.crop.growapp_structure import (
    LocationClass as GrowAppLocationClass,
    CropClass as GrowAppCropClass,
    BatchClass as GrowAppBatchClass,
    BatchEventClass as GrowAppBatchEventClass,
)

from __app__.crop.utils import query_result_to_array
from __app__.crop.constants import (
    GROWAPP_IP,
    GROWAPP_DB,
    GROWAPP_USER,
    GROWAPP_PASSWORD,
    GROWAPP_SCHEMA,
    SQL_CONNECTION_STRING,
    SQL_DBNAME,
    SQL_ENGINE,
)

from __app__.crop.ingress import log_upload_event


def get_growapp_db_session():
    """
    Get an SQLAlchemy session on the GrowApp database.

    Returns
    =======
    session: SQLAlchemy session object
    """
    conn_string = "%s://%s:%s@%s" % (
        SQL_ENGINE,
        GROWAPP_USER,
        parse.quote(GROWAPP_PASSWORD),
        GROWAPP_IP,
    )
    success, log, engine = connect_db(conn_string, GROWAPP_DB)
    if not success:
        logging.info(log)
        return None
    session = session_open(engine)
    return session

def get_cropapp_db_session():
    """
    Get an SQLAlchemy session on the CROP database.

    Returns
    =======
    session: SQLAlchemy session object
    """
    success, log, engine = connect_db(SQL_CONNECTION_STRING, SQL_DBNAME)
    if not success:
        logging.info(log)
        return None
    session = session_open(engine)
    return session


def read_crop_type_data():
    """
    Read from the table of crops in the GrowApp database

    Returns
    =======
    crop_data: list of dicts
    """
