# proof-of-concept script, at this point just copy weather data, but make expandable
# Assume that whatever table we want to copy has a "timestamp" column, and use this to
# identify missing rows in the target db.

# Usage:
#
# python copy_test_to_prod_db.py --start_date <YYYY-mm-dd> --end_date <YYYY-mm-dd> --dbclass <ClassName>
#   where <ClassName> is the name of a class defined in structure.py corresponding to a database table,
#   e.g. "ReadingsWeatherData".

# The script will then prompt you to say which columns you want to copy over, or, if you don't want to
# copy one, it will let you insert a value by hand (or leave blank to let sqlalchemy fill for you)

# Notes:
#   * If running from this directory, need to have '..' in your PYTHONPATH
#   * Need to set environment variables from .secrets/crop.sh, and additionally, some
#     some new environment variables
#     CROP_SRC_SQL_SERVER, CROP_SRC_SQL_PASS, CROP_DEST_SQL_SERVER, CROP_DEST_SQL_PASS
#     corresponding to the server names and passwords for the source and destination databases
#   * The database table that you want to copy must have a 'timestamp' field, with type Datetime.

import os
import argparse
from urllib import parse
from datetime import datetime
from sqlalchemy import and_
from __app__.crop.constants import SQL_DBNAME, SQL_ENGINE, SQL_PORT
from __app__.crop.db import connect_db, session_open, session_close
from __app__.crop import structure


def get_connection_string(src_or_dest):
    """
    Construct a database connection string from server, username, password etc.

    Parameters:
    ===========
    src_or_dest: str, must be 'src' or 'dest', for source or destination databases.

    Returns:
    ========
    connection_string: str
    """
    if src_or_dest == "src":
        try:
            SQL_SERVER = os.environ["CROP_SRC_SQL_SERVER"]
            SQL_PASSWORD = os.environ["CROP_SRC_SQL_PASS"]
        except:
            print("Need to set environment variables CROP_SRC_SQL_SERVER, CROP_SRC_SQL_PASS")
            return None
    elif src_or_dest == "dest":
        try:
            SQL_SERVER = os.environ["CROP_DEST_SQL_SERVER"]
            SQL_PASSWORD = os.environ["CROP_DEST_SQL_PASS"]
        except:
            print("Need to set environment variables CROP_DEST_SQL_SERVER, CROP_DEST_SQL_PASS")
            return None
    else:
        print("Error: need to specify 'src' or 'dest'")
    SQL_USERNAME = os.environ["CROP_SQL_USERNAME"]
    SQL_USER = f"{SQL_USERNAME}@{SQL_SERVER}"
    SQL_HOST = f"{SQL_SERVER}.postgres.database.azure.com"
    SQL_CONNECTION_STRING = "%s://%s:%s@%s:%s" % (
        SQL_ENGINE,
        SQL_USER,
        parse.quote(SQL_PASSWORD),
        SQL_HOST,
        SQL_PORT,
    )
    return SQL_CONNECTION_STRING


def get_db_session(src_or_dest):
    """
    Get an SQLAlchemy session object, for either the source or destination database

    Parameters
    ==========
    src_or_dest: str, must be 'src' or 'dest', for source or destination database

    Returns:
    ========
    session: SQLAlchemy session object
    """
    database = SQL_DBNAME
    conn_string = get_connection_string(src_or_dest)
    success, log, engine = connect_db(conn_string, database)
    session = session_open(engine)
    return session


def get_src_data(DbClass, date_from, date_to, columns_to_copy):
    """
    Read all attributes of the selected table, and put selected columns into a dictionary

    Parameters
    ==========
    DbClass: SQLAlchemy ORM class, as defined in structure.py
    date_from: datetime
    date_to: datetime
    columns_to_copy: list of str, which columns to copy from old db to new.

    Returns
    =======
    all_results: list of dicts, one dict per row, keys of dict taken from columns_to_copy.
    """
    session = get_db_session("src")
    results = session.query(
        DbClass
    ).filter(
        and_(
            DbClass.timestamp >= date_from,
            DbClass.timestamp <= date_to,
        )
    ).all()
    all_results = []
    for r in results:
        result_dict = {}
        for col in columns_to_copy:
            result_dict[col] = getattr(r, col)
        all_results.append(result_dict)
    session_close(session)
    return all_results


def get_existing_dest_data(DbClass, date_from, date_to):
    """
    Get timestamps of existing data

    Parameters
    ==========
    DbClass: SQLAlchemy ORM class, as defined in structure.py
    date_from: datetime
    date_to: datetime

    Returns:
    ========
    timestamps: list of datetime objects
    """
    session = get_db_session("dest")
    results = session.query(
        DbClass.timestamp
    ).filter(
        and_(
            DbClass.timestamp >= date_from,
            DbClass.timestamp <= date_to,
        )
    ).all()

    timestamps = [ r.timestamp for r in results ]
    session_close(session)
    return timestamps


def categorize_columns(DbClass):
    """
    Prompt the user to choose whether to copy a column from the old database to the new.
    If not to be copied, the user can either set a value by hand, that will be applied to all rows,
    or press return in which case it will either be null, or Sqlalchemy will set a value
    (e.g. for 'time_updated').

    Parameters:
    ===========
    DbClass: SQLAlchemy ORM class as defined in structure.py

    Returns:
    ========
    copy_vals: list of str, variables to be copied from source to destination tables
    set_vals: dict, keys are variable names to be set by hand, and vals are values to be set.
    """
    copy_vals = []
    set_vals = {}
    for col in DbClass.__table__.columns.keys():
        # never copy the id
        if col == "id":
            continue
        to_copy = input(f"Would you like to copy values of {col} to from src to dest DB? (y/n): ")
        if to_copy.lower() == "y":
            copy_vals.append(col)
        else:
            set_val = input(f"Enter a value you would like to set {col} to in dest DB (or press return for null): ")
            if len(set_val) > 0:
                set_vals[col] = set_val
    return copy_vals, set_vals


def write_to_destination(DbClass, src_vals, dest_timestamps, set_cols):
    """
    Copy non-overlapping rows from src database to destination database

    Parameters
    ==========
    DbClass: SQLAlchemy ORM class as defined in structure.py
    src_vals: list of dicts, containing values to be copied into rows in destination db.
    dest_timestamps: list of datetime objects, for rows already in destination db.
    set_cols: dict, variables to be set by hand in the destination db

    Returns
    =======
    success: bool

    """
    session = get_db_session("dest")
    write_count = 0
    for sv in src_vals:
        if sv["timestamp"] in dest_timestamps:
            print(f"{sv['timestamp']} already in destination database")
            continue
        new_row = DbClass()
        for k,v in sv.items():
            setattr(new_row,k,v)
        for k,v in set_cols.items():
            setattr(new_row,k,v)
        print(f"adding data for {sv['timestamp']}")
        session.add(new_row)
        write_count += 1
    session.commit()
    session_close(session)
    print(f"Wrote {write_count} rows to destination database")
    return True


def main(args):
    date_from = datetime.strptime(args.start_date, "%Y-%m-%d")
    date_to = datetime.strptime(args.end_date, "%Y-%m-%d")
    try:
        DbClass = getattr(structure, args.dbclass)
    except(AttributeError):
        print(f"The class name {args.dbclass} was not found in structure.py")
        return
    if type(DbClass).__name__ != "DefaultMeta":
        print(f"Class {args.dbclass} is not a derived class of SQLAlchemy BASE")
        return
    if "timestamp" not in dir(DbClass):
        print(f"Class {args.dbclass} does not have a column 'timestamp'.  Sorry.")
        return
    vals_to_copy, vals_set_by_hand = categorize_columns(DbClass)
    print("Will copy values", vals_to_copy)
    print("Will set values", vals_set_by_hand)
    src_values = get_src_data(DbClass, date_from, date_to, vals_to_copy)
    print(f"Found {len(src_values)} entries in source db")
    existing_timestamps = get_existing_dest_data(DbClass, date_from, date_to)
    print(f"Found {len(existing_timestamps)} entries in destination db")
    success = write_to_destination(DbClass, src_values, existing_timestamps, vals_set_by_hand)
    if success:
        print("Finished OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="copy missing data from one db to another")
    parser.add_argument("--start_date", type=str, help="format YYYY-MM-DD", required=True)
    parser.add_argument("--end_date", type=str, help="format YYYY-MM-DD", required=True)
    parser.add_argument("--dbclass", type=str, help="name of SQLAlchemy class from structure.py", required=True)
    args = parser.parse_args()
    main(args)
