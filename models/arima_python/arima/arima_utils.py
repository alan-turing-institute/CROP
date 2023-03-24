import os
import pandas as pd
from pathlib import Path

from cropcore.db import connect_db, session_open, session_close
from cropcore.constants import SQL_CONNECTION_STRING, SQL_DBNAME

from cropcore.structure import (
    ModelClass,
    ModelMeasureClass,
    ModelScenarioClass,
    SensorClass,
)


# Relative import doesn't work if we are in same dir as this module
if os.getcwd() == os.path.dirname(os.path.realpath(__file__)):
    from config import config
else:
    from .config import config


def get_measure_id(measure_name, session=None):
    """Get the database ID of a measure of a given name, assuming the BAU scenario."""
    if session is None:
        session = get_sqlalchemy_session()
    query = (
        session.query(ModelMeasureClass.id)
        .join(
            ModelScenarioClass, ModelScenarioClass.id == ModelMeasureClass.scenario_id
        )
        .filter(
            (ModelMeasureClass.measure_name == measure_name)
            & (ModelScenarioClass.scenario_type == "BAU")
        )
    )
    measure_id = session.execute(query).fetchfirst()[0]
    return measure_id


def get_sensor_id(sensor_name, session=None):
    """Get the database ID of a sensor of a given name."""
    if session is None:
        session = get_sqlalchemy_session()
    query = session.query(SensorClass.id).filter(SensorClass.name == sensor_name)
    sensor_id = session.execute(query).fetchfirst()[0]
    return sensor_id


def get_sqlalchemy_session(connection_string=None, dbname=None):
    """
    For other functions in this module, if no session is provided as an argument,
    they will call this to get a session using default connection string.
    """
    if not connection_string:
        connection_string = SQL_CONNECTION_STRING
    if not dbname:
        dbname = SQL_DBNAME
    status, log, engine = connect_db(connection_string, dbname)
    session = session_open(engine)
    return session


def get_model_id(model_name="arima", session=None):
    """
    Find the index of the specified model in the database

    Parameters
    ----------
    model_name: str, name of e.g. Arima model in the ModelClass table in the db.
    session: sqlalchemy session.  If None, use default db.

    Returns
    -------
    model_id: int, or None if not found
    """
    if not session:
        session = get_sqlalchemy_session()
    query = session.query(ModelClass.id, ModelClass.model_name).filter(
        ModelClass.model_name == model_name
    )
    result = session.execute(query).fetchone()
    if result:
        return result[0]
    return None
