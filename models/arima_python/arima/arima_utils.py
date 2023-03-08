import os
import pandas as pd
from pathlib import Path

from cropcore.db import connect_db, session_open, session_close
from cropcore.constants import SQL_CONNECTION_STRING, SQL_DBNAME

# Relative import doesn't work if we are in same dir as this module
if os.getcwd() == os.path.dirname(os.path.realpath(__file__)):
    from config import config
else:
    from .config import config

def get_sqlalchemy_session(connection_string=None, dbname=None):
    """
    For other functions in this module, if no session is provided as an argument,
    they will call this to get a session using default connection string.
    """
    if not connection_string:
        connection_string = SQL_CONNECTION_STRING
    if not dbname:
        dbname = SQL_DBNAME
    status, log, engine = connect_db(connection_string, dbname)
    session = session_open(engine)
    return session