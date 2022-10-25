"""
Python module to create a new database table (corresponding to a SQLAlchemy class)
"""

from sqlalchemy.exc import ProgrammingError
from sqlalchemy.engine import Engine
from .structure import BASE


def create_table(engine: Engine, TableClass: BASE):
    """
    Create a new database table (corresponding to a SQLAlchemy class from structure.py)
    if it doesn't already exist

    Arguments:
        engine: SQLAlchemy engine, connected to the database
        TableClass: the SQLAlchemy class (corresponding to a database table from structure.py)

    Returns:
        success: True if a new table is created, False otherwise
        log: log message
    """
    success = False
    log = "Table already exists in database"
    try:
        TableClass.__table__.create(bind=engine)
        success = True
        log = "New DB table created"
    except ProgrammingError:
        # The table already exists
        pass
    return success, log
