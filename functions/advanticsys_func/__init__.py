"""
Importing advanticsys data using Azure FunctionApp.
"""

import os
import logging

from io import StringIO

import pandas as pd
import azure.functions as func

from __app__.crop.constants import (
    CONST_ADVANTICSYS,
    SQL_ENGINE,
)
from __app__.crop.utils import make_conn_string
from __app__.crop.ingress import import_data, log_upload_event


def advanticsys_import(blobin: func.InputStream):
    """
    The main advanticsys Azure Function routine.

    """

    logging.info(
        f"Starting advanticsys sensor data import process:\n"
        f"Name: {blobin.name}\n"
        f"Blob Size: {blobin.length} bytes"
    )

    # reading in data as pandas dataframe
    data_str = str(blobin.read(), "utf-8")
    data_stream = StringIO(data_str)
    data_df = pd.read_csv(data_stream)

    # getting the environmental parameters
    user = "{}".format(os.environ["CROP_SQL_USER"].strip())
    password = "{}".format(os.environ["CROP_SQL_PASS"].strip())
    host = "{}".format(os.environ["CROP_SQL_HOST"].strip())
    port = "{}".format(os.environ["CROP_SQL_PORT"].strip())
    database = "{}".format(os.environ["CROP_SQL_DBNAME"].strip())

    # uploading data to the database
    status, log = import_data(
        data_df, CONST_ADVANTICSYS, user, password, host, port, database
    )

    # Logging the advanticsys sensor data upload event
    conn_string = make_conn_string(SQL_ENGINE, user, password, host, port)

    log_status, log_err = log_upload_event(
        CONST_ADVANTICSYS, blobin.name, status, log, conn_string
    )

    if status:

        logging.info(
            f"SUCCESS: advanticsys sensor data import process finished:\n"
            f"Name: {blobin.name}\n"
            f"Blob Size: {blobin.length} bytes\n"
            f"Info: {log}\n"
            f"Log: {log_status} {log_err}"
        )

    else:

        logging.info(
            f"ERROR: advanticsys sensor data import process failed:\n"
            f"Name: {blobin.name}\n"
            f"Blob Size: {blobin.length} bytes\n"
            f"Info: {log}\n"
            f"Log: {log_status} {log_err}"
        )
