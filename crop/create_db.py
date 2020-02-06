'''
Module doc string
'''

#import psycopg2
from sqlalchemy import create_engine, inspect
from sqlalchemy_utils import database_exists
from sqlalchemy.ext.declarative.clsregistry import _ModuleMarker
from sqlalchemy.orm import RelationshipProperty, sessionmaker

from crop.constants import (
    SQL_DEFAULT_DBNAME,
    SQL_DBNAME,
    SQL_CONNECTION_STRING,
)

from crop.structure import BASE


def create_database(sql_connection_string, db_name):
    """
    Function to create a new database
        dbname:pip
    """
    error = False
    log = ""

    # Check if database exists
    if not database_exists(sql_connection_string + db_name):
        try: 
            #On postgres, the postgres database is normally present by default. 
            #Connecting as a superuser (eg, postgres), allows to connect and create a new db.
            engine = create_engine(sql_connection_string + SQL_DEFAULT_DBNAME)

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
            newengine = create_engine(sql_connection_string + db_name)
            BASE.metadata.create_all(newengine)

            conn.close()
        except: 
            error = True
            log = "Error creating a new database"
    
    return error, log

def check_table_exists(sql_connection_string, table_name):
    """
    Checks if table exists..
    args:
    returns:
    """

    # Creates a connection to the db with name db_name
    try: 
        engine = create_engine(sql_connection_string)
    except: 
        return False, "Cannot find db"

    # Accesses databases
    iengine = inspect(engine)

    # Accesses tables
    tables = iengine.get_table_names()

    if table_name in tables:
        return True, None
    else: 
        return False, "Table <{}> not found".format(table_name)


def check_database_structure (sql_connection_string):

    """Check whether the current database matches the models declared in model base.

    Currently we check that all tables exist with all columns. What is not checked

    * Column types are not verified

    * Relationships are not verified at all (TODO)

    :param Base: Declarative Base for SQLAlchemy models to check

    :param session: SQLAlchemy session bound to an engine

    :return: True if all declared models have corresponding tables and columns.
    """
    error = False
    log = ""

    #Creates a connection to the db with name db_name
    try: 
        engine = create_engine("{}{}".format(sql_connection_string, db_name))
    except: 
        return True, "Cannot find db " + db_name

    # Creates a new session
    session = sessionmaker()
    
    # Binds the engine to this session
    session.configure(bind=engine)
    s = session()

    # Accesses databases
    iengine = inspect(engine)

    # Accesses tables
    tables = iengine.get_table_names()
    #print (tables)

    if (len(tables))>0: 
        for name, klass in BASE._decl_class_registry.items():

            table = klass.__tablename__
            if table in tables: 
                #checks all columns are found
                columns = [c["name"] for c in iengine.get_columns(table)]
                print ("columns: ", columns)
                mapper = inspect(klass)
                print ("mapper: ", mapper)

                for column_prop in mapper.attrs:
                    if isinstance(column_prop, RelationshipProperty):
                        #To do add checks for relations
                        print ("passed")
                        pass
                    else: 
                        for column in column_prop._columns_are_mapped:
                            if not column.key in columns:
                                return True, "Model %s declares column %s which does not exist in db", klass, column.key

            else:
                return True, "Model %s declares table %s which does not exist in db", klass, table
        
    else: return True, "No tables found in the db"
    
    print ("it worked")
    return error, log

