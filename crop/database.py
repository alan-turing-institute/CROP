'''
Module for interactions with the database
'''

import psycopg2

from .constants import (
    PSYCOPG2_SQL_CONNECTION_STRING_DEFAULT
)

def connect_to_db():
    """
    Connects to the SQL DB and returns connection object.
    """

    return psycopg2.connect(PSYCOPG2_SQL_CONNECTION_STRING_DEFAULT) 

def disconnect_from_db(conn):
    """
    Closes the connection to the db.
        conn: connection object
    """
    
    conn.close()