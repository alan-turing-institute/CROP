'''
Module doc string
'''

#import psycopg2
from sqlalchemy import create_engine, inspect
from sqlalchemy_utils import database_exists
from sqlalchemy.ext.declarative.clsregistry import _ModuleMarker
from sqlalchemy.orm import RelationshipProperty

from crop.constants import (
    SQL_DEFAULT_DBNAME
)

from crop.structure import BASE


def create_database(SQL_CONNECTION_STRING, db_name):
    """
    Function to create a new database
        dbname:pip
    """
    error = False
    log = ""

    # Check if database exists
    if not database_exists(SQL_CONNECTION_STRING + db_name):
        try: 
            #On postgres, the postgres database is normally present by default. 
            #Connecting as a superuser (eg, postgres), allows to connect and create a new db.
            engine = create_engine(SQL_CONNECTION_STRING + SQL_DEFAULT_DBNAME)

            #You cannot use engine.execute() directly, because postgres does not allow to create
            # databases inside transactions, inside which sqlalchemy always tries to run queries.
            # To get around this, get the underlying connection from the engine:
            conn = engine.connect()

            #But the connection will still be inside a transaction, so you have to end the open
            # transaction with a commit:
            conn.execute("commit")

            #And you can then proceed to create the database using the proper PostgreSQL command for it.
            conn.execute("create database " + db_name)
            print ("created db " + db_name)

            #creates a new engine using the new database url and adds the defined tables and columns
            newengine = create_engine(SQL_CONNECTION_STRING + db_name)
            BASE.metadata.create_all(newengine)

            conn.close()
        except: 
            error = True
            log = "Error creating a new database"
    
    return error, log



def check_database_structure (Base, session):
    """Check whether the current database matches the models declared in model base.

    Currently we check that all tables exist with all columns. What is not checked

    * Column types are not verified

    * Relationships are not verified at all (TODO)

    :param Base: Declarative Base for SQLAlchemy models to check

    :param session: SQLAlchemy session bound to an engine

    :return: True if all declared models have corresponding tables and columns.
    """
    engine = session.get_bind()
    iengine = inspect(engine)

    error = False

    tables = iengine.get_table_names()
