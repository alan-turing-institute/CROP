import os
import logging
import azure.functions as func

from io import StringIO
import pandas as pd

SERVER_TYPE = "advantix"

def advantix_upload(blobin: func.InputStream):

    logging.info(f"Starting advantix sensor data import process: \n"
                 f"Name: {blobin.name}\n"
                 f"Blob Size: {blobin.length} bytes")

    # reading in data as pandas dataframe
    data_str = str(blobin.read(), 'utf-8')
    data_stream = StringIO(data_str) 
    data_df = pd.read_csv(data_stream)

    # TODO: Upload data to the sql server.
    server = "{}".format(os.environ["AZURE_SQL_SERVER"].strip())
    db = "{}".format(os.environ["AZURE_SQL_DBNAME"].strip())
    user = "{}".format(os.environ["AZURE_SQL_USER"].strip())
    password = "{}".format(os.environ["AZURE_SQL_PASS"].strip())
    port = "{}".format(os.environ["AZURE_SQL_PORT"].strip())

    # data ingress function
    # status, error = function(data_df, SERVER_TYPE, server, db, user, password, port)
    
    status = False
    error = "test error"

    if not status:
        # TODO: send email to admins with an error functionality
        
        logging.info(f"ERROR: advantix sensor data import process failed: \n"
                     f"Name: {blobin.name}\n"
                     f"Blob Size: {blobin.length} bytes\n"
                     f"Error: {error}")
    else:
        logging.info(f"COMPLETED: advantix sensor data import process finished: \n"
                     f"Name: {blobin.name}\n"
                     f"Blob Size: {blobin.length} bytes")

    