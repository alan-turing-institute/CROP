import logging
import psycopg2
import datetime
from .config import config


def openConnection():
    """Connect to the PostgreSQL database server"""
    conn = None
    try:
        # read DB connection parameters
        params = config()

        # connect to the PostreSQL server
        logging.info("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**params)

    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(error)
    finally:
        return conn


def closeConnection(conn):
    """Close the PostgreSQL connection"""
    if conn is not None:
        conn.close()
        logging.info("Database connection closed.")


def printRowsHead(rows, numrows=0):
    """Log the number of rows retrieved from the database"""
    logging.info("Printing:{0} of {1}".format(numrows, len(rows)))
    if numrows == 0:
        for row in rows[: len(rows)]:
            logging.info(row)
    else:
        for row in rows[:numrows]:
            logging.info(row)


def getData(query):
    conn = None
    try:
        conn = openConnection()
        cur = conn.cursor()  # create a cursor
        cur.execute(query)
        rows = cur.fetchall()
        printRowsHead(rows, numrows=10)
        cur.close()  # close the communication with the PostgreSQL

        logging.info(f"Got data from {query} - returning {len(rows)} rows")
        return rows
    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(error)
    finally:
        closeConnection(conn=conn)
