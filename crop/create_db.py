'''
Module doc string
'''

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists

from .constants import (
    SQL_CONNECTION_STRING_DEFAULT,
    SQL_CONNECTION_STRING_CROP,
    SQL_DBNAME
)

from .structure import BASE

def create_database(db_name):
    """
    Funtion to create a new database
        dbname:
    """

    if not database_exists(SQL_CONNECTION_STRING_CROP):
        #On postgres, the postgres database is normally present by default. 
        #Connecting as a superuser (eg, postgres), allows to connect and create a new db.
        engine = create_engine(SQL_CONNECTION_STRING_DEFAULT)

        #You cannot use engine.execute() directly, because postgres does not allow to create
        # databases inside transactions, inside which sqlalchemy always tries to run queries.
        # To get around this, get the underlying connection from the engine:
        conn = engine.connect()

        #But the connection will still be inside a transaction, so you have to end the open
        # transaction with a commit:
        conn.execute("commit")

        #And you can then proceed to create the database using the proper PostgreSQL command for it.
        conn.execute("create database " + db_name)

        newengine = create_engine(SQL_CONNECTION_STRING_CROP)
        BASE.metadata.create_all(newengine)

        conn.close()
    
    else:
        engine = create_engine(SQL_CONNECTION_STRING_CROP)
        BASE.metadata.create_all(engine)

