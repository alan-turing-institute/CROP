"""
Python module to perform data ingress operations

"""

import pandas as pd
from crop.ingress import advantix_df_checks
from crop.create_db import create_database

def advantix_SQL_insert(pd_df_raw, server, db, user, password, port):
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

    status = True
    error = ""


    # Checks if db exists, if not tries to create it. 
    status, error= create_database(db_name)
    return status, error

    # Try to establish connection to the db
    status, error= connect_to_database(db), "cannot connect to database"
    return status, error



    if not isinstance(pd_df_raw, pd.DataFrame):
        return False, "Not a pandas dataframe"
    
    if pd_df_raw.empty:
        return False, "Dataframe empty"

    # Checks structure
    success, log, pd_df = advantix_df_checks(pd_df_raw)
    if not success: 
        return success, log

    
 