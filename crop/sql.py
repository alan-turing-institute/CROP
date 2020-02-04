"""
Python module to perform data ingress operations

"""

import pandas as pd
from sqlalchemy import create_engine
from crop.ingress import advantix_df_checks
from crop.create_db import create_database
from crop.constants import (
    CWD,
    SQL_DBNAME,
    SQL_CONNECTION_STRING,
    CONST_ADVANTIX_TEST_1
)



def advantix_SQL_insert(server, user, password, host, port, db_name, pd_df_raw):
    """
    Function description

    Args:
        pd_df - 
        server -
        db -
        user -
        password -
        port -

    Returns:
        success - status
        log - error message
    """

    error = False
    log = ""


    # Checks if db exists, if not creates it with tables. 
    error, log = create_database(SQL_CONNECTION_STRING, db_name)
    if error: return error, log
    
    # Creates an engine
    try: 
        engine = create_engine(SQL_CONNECTION_STRING + db_name)
    except:
        error = True
        log = "Error connecting to the database"
        return error, log

    # Checks structure
    #TODO

    # Checks advantix ingress
    success, log, pd_df = advantix_df_checks(pd_df_raw)
    if not success: return success, log

    
 