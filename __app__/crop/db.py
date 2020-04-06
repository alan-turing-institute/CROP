"""
Module for the main functions to create a new database with SQLAlchemy and Postgres,
drop database, and check its structure.
"""

from sqlalchemy import create_engine, inspect
from sqlalchemy_utils import database_exists, drop_database
from sqlalchemy.orm import RelationshipProperty, sessionmaker
from sqlalchemy.ext.declarative.clsregistry import _ModuleMarker
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from __app__.crop.constants import SQL_DEFAULT_DBNAME
from __app__.crop.structure import BASE


def create_database(conn_string, db_name):
    """
    Function to create a new database
    -sql_connection_string: a string that holds an address to the db
    -dbname: name of the db (string)
    return: True, None if the db is created or is already created
    """

    # Create connection string
    db_conn_string = "{}/{}".format(conn_string, db_name)

    # Create a new database
    if not database_exists(db_conn_string):
        try:
            # On postgres, the postgres database is normally present by default.
            # Connecting as a superuser (eg, postgres), allows to connect and create a new db.
            def_engine = create_engine("{}/{}".format(conn_string, SQL_DEFAULT_DBNAME))

            # You cannot use engine.execute() directly, because postgres does not allow to create
            # databases inside transactions, inside which sqlalchemy always tries to run queries.
            # To get around this, get the underlying connection from the engine:
            conn = def_engine.connect()

            # But the connection will still be inside a transaction, so you have to end the open
            # transaction with a commit:
            conn.execute("commit")

            # Then proceed to create the database using the PostgreSQL command.
            conn.execute("create database " + db_name)

            # Connects to the engine using the new database url
            _, _, engine = connect_db(conn_string, db_name)
            # Adds the tables and columns from the classes in module structure
            BASE.metadata.create_all(engine)

            conn.close()
        except:
            return False, "Error creating a new database"
    return True, None


def connect_db(conn_string, db_name):
    """
    Function to connect to a database
    -conn_string: the string that holds the connection to postgres
    -dbname: name of the database
    return: True, None: if connected to the database,
            engine: returns the engine object
    """

    # Create connection string
    db_conn_string = "{}/{}".format(conn_string, db_name)

    # Connect to an engine
    if database_exists(db_conn_string):
        try:
            engine = create_engine(db_conn_string)
        except:
            return False, "Cannot connect to db: %s" % db_name, None
    else:
        return False, "Cannot find db: %s" % db_name, None

    return True, None, engine


def drop_db(conn_string, db_name):
    """
    Function to drop db
    *WHat it doesnt do: drop individual table/column/values
    -conn_string: the string that holds the connection to postgres
    -dbname: name of the database
    return: True, None if the db is dropped.
    """

    # Connection string
    db_conn_string = "{}/{}".format(conn_string, db_name)

    if database_exists(db_conn_string):
        # Connect to the db
        _, _, engine = connect_db(conn_string, db_name)

        # Disconnects all users from the db we want to drop
        try:
            connection = engine.connect()
            connection.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            version = connection.dialect.server_version_info
            pid_column = "pid" if (version >= (9, 2)) else "procpid"
            text = """
            SELECT pg_terminate_backend(pg_stat_activity.%(pid_column)s)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '%(database)s'
              AND %(pid_column)s <> pg_backend_pid();
            """ % {
                "pid_column": pid_column,
                "database": db_name,
            }
            connection.execute(text)

            # Drops db
            drop_database(db_conn_string)

        except:
            return False, "cannot drop db %s" % db_name
    return True, None


def check_database_structure(engine):

    """
    Check whether the current database matches the models declared in model base.

    Currently we check that all tables exist with all columns. What is not checked
    * Column types are not verified
    * Relationships are not verified

    engine: The db engine

    return: True, None if all declared models have corresponding tables and columns.
    """

    # Accesses sql db
    iengine = inspect(engine)

    # gets table names from sql server in python list
    sql_tables = iengine.get_table_names()

    if sql_tables:

        # goes through the sqlalchemy classes
        for _, sql_class in BASE._decl_class_registry.items():

            # filter out objecs that are not classes (e.g.base)
            if isinstance(sql_class, _ModuleMarker):
                continue
            tablename = sql_class.__tablename__

            # checks if all tablenames in class exist in sql
            if tablename in sql_tables:
                # gets the column names of each table in sql
                columns = [c["name"] for c in iengine.get_columns(tablename)]

                # gets objects in each class in the form of:
                # Readings_Advanticsys.sensor_relationship
                mapper = inspect(sql_class)

                for obj in mapper.attrs:
                    print(obj)

                    # checks if the object is a relationship
                    if isinstance(obj, RelationshipProperty):
                        # To do add checks for relations
                        pass
                    else:
                        # assume normal flat column
                        if not obj.key in columns:
                            return (
                                False,
                                "Model %s declares column %s which\
                            does not exist"
                                % (sql_class, columns.key),
                            )
            else:
                return (
                    False,
                    "Model %s declares table %s which doesn't exist",
                    sql_class,
                    tablename,
                )

    else:
        return False, "No tables found in the db"

    return True, None


def session_open(engine):
    """
    Opens a new connection/session to the db and binds the engine
    -engine: the connected engine
    """
    Session = sessionmaker()
    Session.configure(bind=engine)
    return Session()


def session_close(session):
    """
    Closes the current open session
    -session: an open session
    """
    session.commit()
    session.close()
