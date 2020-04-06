import os
import logging
import azure.functions as func

from io import StringIO
import pandas as pd

from __app__.crop.constants import CONST_ADVANTICSYS

# TODO: change to the real Python module
from __app__.crop.temp_ingress import import_data

def advanticsys_import(blobin: func.InputStream):

    logging.info(f"Starting advanticsys sensor data import process: \n"
                 f"Name: {blobin.name}\n"
                 f"Blob Size: {blobin.length} bytes")

    # reading in data as pandas dataframe
    data_str = str(blobin.read(), 'utf-8')
    data_stream = StringIO(data_str)
    data_df = pd.read_csv(data_stream)
    
    # getting the environmental parameters
    host = "{}".format(os.environ["CROP_SQL_HOST"].strip())
    db = "{}".format(os.environ["CROP_SQL_DBNAME"].strip())
    user = "{}".format(os.environ["CROP_SQL_USER"].strip())
    password = "{}".format(os.environ["CROP_SQL_PASS"].strip())
    port = "{}".format(os.environ["CROP_SQL_PORT"].strip())

    # uploading data to tthe database
    status, error = import_data(data_df, CONST_ADVANTICSYS, 
        user, password, host, port, db)
    
    logging.info(f"!!!!!!")
    logging.info(f"status: {status}")
    logging.info(f"error: {error}")
    logging.info(f"!!!!!!")
    logging.info(f"{CONST_ADVANTICSYS}")
    logging.info(f"!!!!!!")

    status = False
    error = "test error"

    if status:
        logging.info(f"COMPLETED: advanticsys sensor data import process finished: \n"
                     f"Name: {blobin.name}\n"
                     f"Blob Size: {blobin.length} bytes")
    else:
        # TODO: send email to admins with an error functionality
        
        logging.info(f"ERROR: advanticsys sensor data import process failed: \n"
                     f"Name: {blobin.name}\n"
                     f"Blob Size: {blobin.length} bytes\n"
                     f"Error: {error}")

    