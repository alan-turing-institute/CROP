import os
import logging
import azure.functions as func

from io import StringIO
import pandas as pd

def advantix_upload(blobin: func.InputStream):

    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {blobin.name}\n"
                 f"Blob Size: {blobin.length} bytes")

    # reading in data as pandas dataframe
    data_str = str(blobin.read(), 'utf-8')
    data_stream = StringIO(data_str) 
    data_df = pd.read_csv(data_stream)

    # TODO: Upload data to the sql server.
    server = "{}".format(os.environ["AZURE_SQL_SERVER"].strip())
    database = "{}".format(os.environ["AZURE_SQL_DBNAME"].strip())
    user = "{}".format(os.environ["AZURE_SQL_USER"].strip())
    password = "{}".format(os.environ["AZURE_SQL_PASS"].strip())
    port = "{}".format(os.environ["AZURE_SQL_PORT"].strip())

    # TODO: send email functionality





    