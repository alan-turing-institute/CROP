"""
Python script to create read-only sql user
"""

import os
import logging
import psycopg2
from psycopg2.extensions import AsIs

logging.basicConfig(level=logging.INFO)

CROP_HOST = os.environ["CROP_SQL_HOST"]
CROP_PORT = os.environ["CROP_SQL_PORT"]
CROP_DBNAME = os.environ["CROP_SQL_DBNAME"].strip().lower()
CROP_USER = os.environ["CROP_SQL_USER"]
CROP_PASSWORD = os.environ["CROP_SQL_PASS"]
CROP_USERNAME = os.environ["CROP_SQL_USERNAME"]

CROP_READER_USER = os.environ["CROP_SQL_READER_USER"]
CROP_READER_PASS = os.environ["CROP_SQL_READER_PASS"]

def delete_reader(conn, cur):
    """
    Deletes data reader user
    Arguments:
        conn: active connection to the posgresql
        cur: active cursor
    """

    logging.info("DROP USER %s", CROP_READER_USER)

    cur.execute("REASSIGN OWNED BY %s TO %s" % (CROP_READER_USER, CROP_USERNAME))
    cur.execute("DROP OWNED BY %s" % CROP_READER_USER)
    cur.execute("DROP USER %s" % CROP_READER_USER)
    conn.commit()

if __name__ == "__main__":
    
    conn = psycopg2.connect(
        host=CROP_HOST, port=CROP_PORT, dbname=CROP_DBNAME, 
        user=CROP_USER, password=CROP_PASSWORD)

    cur = conn.cursor()

    logging.info("CREATE USER %s", CROP_READER_USER)

    try:
        user = AsIs(CROP_READER_USER)
        
        cur.execute("CREATE USER %s WITH ENCRYPTED PASSWORD %s", (user, CROP_READER_PASS, ))
        conn.commit()

        cur.execute("GRANT CONNECT ON DATABASE %s TO %s" % (CROP_DBNAME, CROP_READER_USER))
        cur.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO %s" % (CROP_READER_USER))
        conn.commit()

    except:
        logging.info("CREATE USER %s : FAILED", CROP_READER_USER)
        conn.rollback()

    # delete_reader(conn, cur)

    # Close communication
    cur.close()
    conn.close()

    logging.info("Finished.")
