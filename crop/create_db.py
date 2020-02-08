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
    SQL_CONNECTION_STRING
)

from crop.structure import BASE


def create_database(sql_connection_string, db_name):
    """
    Function to create a new database
        dbname:pip
    """
   
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
            return False, "Error creating a new database"
    return True, None


#create_database(SQL_CONNECTION_STRING, SQL_DBNAME)

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


    #Creates a connection to the db with name db_name
    try: 
        engine = create_engine(sql_connection_string)
    except: 
        return False, "Cannot find db with connection: %s" % sql_connection_string

    # Accesses sql db
    iengine = inspect(engine)

    # gets table names from sql server in python list
    sql_tables = iengine.get_table_names()
    #print (sql_tables)

    if (len(sql_tables))>0:
        #goes through the sqlalchemy classes
        for name, sql_class in BASE._decl_class_registry.items():

            #filter out objecs that are not classes
            if isinstance(sql_class, _ModuleMarker):
                # Not a class (base)
                continue
            tablename = sql_class.__tablename__

            #checks if all tablenames in class exist in sql 
            if tablename in sql_tables: 
                #gets the column names of each table in sql 
                columns = [c["name"] for c in iengine.get_columns(tablename)]

                #print ("columns: ", columns)
                #gets all objects in each class in the form of: Readings_Advantix.sensor_relationship
                mapper = inspect(sql_class)
                for object in mapper.attrs:
                    print (object)
                    #checks if the object is a relationship
                    if isinstance(object, RelationshipProperty):
                        #To do add checks for relations
                        pass
                    else: 
                        print (object.key)
                        #assume normal flat column
                        if not object.key in columns:
                            return False, "Model %s declares column %s which does not exist in db" % (sql_class_class, columns.key)

            else:
                return False, "Model %s declares table %s which does not exist in db", sql_class, tablename
        
    else: return False, "No tables found in the db"
    #print ("it worked")

    return True, None

#conn_string = "{}{}".format(SQL_CONNECTION_STRING, SQL_DBNAME)
#check_database_structure(conn_string)