import os
import pandas as pd
from pathlib import Path

from cropcore.db import connect_db, session_open, session_close
from cropcore.constants import SQL_CONNECTION_STRING, SQL_DBNAME
from cropcore.model_data_access import get_sqlalchemy_session
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
    result = session.execute(query).fetchone()
    if result:
        return result[0]
    return None


def get_sensor_id(sensor_name, session=None):
    """Get the database ID of a sensor of a given name."""
    if session is None:
        session = get_sqlalchemy_session()
    query = session.query(SensorClass.id).filter(SensorClass.name == sensor_name)
    result = session.execute(query).fetchone()
    if result:
        return result[0]
    return None


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
