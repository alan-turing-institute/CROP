#!/usr/bin/python
"""
Script that creates (if needed) a database in an existing PostgreSQL server and uploads
syntetic data to it.
"""

import argparse

import sys
import pandas as pd

from core.structure import UserClass

from core.constants import SQL_CONNECTION_STRING


from core.db import (
    connect_db,
    session_open,
    session_close,
)


def error_message(message):
    """
    Prints error message.

    """

    print(f"ERROR: {message}")
    sys.exit()


def insert_user_data(engine):
    """
    Bulk inserts users data.

    Arguments:
        engine: SQL engine object
    """

    users_df = pd.read_csv("users.csv")

    assert not users_df.empty

    # Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)

    for user_row in users_df.iterrows():

        data = UserClass(
            username=user_row[1]["username"],
            email=user_row[1]["email"],
            password=user_row[1]["password"],
        )

        session.add(data)

    session_close(session)


def main(db_name):
    """
    Main routine.

    Arguments:
        db_name: Database name
    """

    # creating an engine
    status, log, engine = connect_db(SQL_CONNECTION_STRING, db_name)

    if not status:
        error_message(log)

    insert_user_data(engine)


if __name__ == "__main__":

    # Command line arguments
    PARSER = argparse.ArgumentParser(
        description="Uploads syntetic data to a PostgreSQL database."
    )
    PARSER.add_argument("dbname", default=None, help="Database name")

    # Makes sure that the database exists (creates it if needed.)
    ARGS, _ = PARSER.parse_known_args()

    main((ARGS.dbname).strip())

    print("Finished.")
