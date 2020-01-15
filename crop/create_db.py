'''
Module doc string
'''

#import psycopg2
import sqlalchemy as sqla


def create_database(dbname):
    """
    Funtion to create a new database
        dbname:
    """

    #On postgres, three databases are normally present by default. If you are able to connect
    # as a superuser (eg, the postgres role), then you can connect to the postgres or template1
    # databases. The default pg_hba.conf permits only the unix user named postgres to use the
    # postgres role, so the simplest thing is to just become that user. At any rate, create an
    # engine as usual with a user that has the permissions to create a database
    engine = sqla.create_engine('postgresql://postgres:crop@localhost:5433/postgres')

    #You cannot use engine.execute() however, because postgres does not allow you to create
    # databases inside transactions, and sqlalchemy always tries to run queries in a transaction.
    # To get around this, get the underlying connection from the engine:
    conn = engine.connect()

    #But the connection will still be inside a transaction, so you have to end the open
    # transaction with a commit:
    conn.execute("commit")

    #And you can then proceed to create the database using the proper PostgreSQL command for it.
    conn.execute("create database " + dbname)
    conn.close()
