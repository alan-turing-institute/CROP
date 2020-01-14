import psycopg2
import sqlalchemy as sa
from sqlalchemy import (create_engine, ForeignKey, MetaData, Table, Float, Column, Integer, String, DateTime, Text)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy_utils import database_exists

newdb = 'test2' 

def create_database():
    #On postgres, three databases are normally present by default. If you are able to connect as a superuser (eg, the postgres role), then you can connect to the postgres or template1 databases. The default pg_hba.conf permits only the unix user named postgres to use the postgres role, so the simplest thing is to just become that user. At any rate, create an engine as usual with a user that has the permissions to create a database
    engine = create_engine('postgresql://postgres:crop@localhost:5433/postgres')

    #You cannot use engine.execute() however, because postgres does not allow you to create databases inside transactions, and sqlalchemy always tries to run queries in a transaction. To get around this, get the underlying connection from the engine:
    conn = engine.connect()

    #But the connection will still be inside a transaction, so you have to end the open transaction with a commit:
    conn.execute("commit")

    #And you can then proceed to create the database using the proper PostgreSQL command for it.
    conn.execute("create database test2")
    conn.close()   


def create_tables():
    #access the newly created database
    engine = create_engine('postgresql://postgres:crop@localhost:5433/'+ newdb)
    #get a list of existing tables
    table_names = sa.inspect(engine).get_table_names()
    print (table_names)

    #check if a specific table doesn't exist
    if not engine.dialect.has_table(engine, 'tested'):  # If table don't exist, Create.
        print ("table doesnt exist")
        metadata = MetaData(engine)
        # Create a table with the appropriate Columns
        # Implement the creation
        metadata.create_all()

if database_exists('postgresql://postgres:crop@localhost:5433/'+ newdb):
    create_tables()

else:
    create_database()
