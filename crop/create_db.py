'''
Module doc string
'''

#import psycopg2
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists

from crop.constants import (
    SQL_CONNECTION_STRING_DEFAULT,
    SQL_CONNECTION_STRING_CROP,
    SQL_DBNAME
)

from crop.structure import BASE

def create_database(db_name):
    """
    Funtion to create a new database
        dbname:pip
    """
    success= True
    log = ""

    if not database_exists(SQL_CONNECTION_STRING_CROP):
        try: 
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
            print ("created db" + db_name)

            #creates a new engine using the new database url and adds the defined tables and columns
            newengine = create_engine(SQL_CONNECTION_STRING_CROP)
            #BASE.metadata.create_all(newengine)

            conn.close()
        except: 
            success = False
            log = "Error creating a new database"
    
    return success, log




        
