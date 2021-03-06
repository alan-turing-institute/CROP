"""
Python module for misc sensor functions.
"""

from pandas import DataFrame
from sqlalchemy import and_

from __app__.crop.structure import (
    TypeClass,
    ReadingsZensieTRHClass,
)

def find_sensor_type_id(session, sensor_type):
    """
    Function to find sensor type id by name.

    Args:
        session: sqlalchemy active seession object
        sensor_type: sensor type name

    Returns:
        type_id: type id, -1 if not found
        log: message if not found
    """

    type_id = -1
    log = ""

    # Gets the the assigned int id of sensor type

    try:
        type_id = (
            session.query(TypeClass)
            .filter(TypeClass.sensor_type == sensor_type)
            .first()
            .id
        )
    except:
        log = "Sensor type {} was not found.".format(sensor_type)

    return type_id, log


def get_zensie_trh_sensor_data(session, sensor_id, date_from, date_to):
    """
    Returns zensie trh sensor data for specific period of time as pandas data frame.

    Arguments:
        session: sqlalchemy active seession object
        sensor_id: sensor id
        date_from: date range from
        date_to: date range to
    Returns:
        data_df: data frame containing sensor data for specific period of time
    """

    query = session.query(
        ReadingsZensieTRHClass.timestamp,
    ).filter(
        and_(
            ReadingsZensieTRHClass.sensor_id == sensor_id,
            ReadingsZensieTRHClass.timestamp >= date_from,
            ReadingsZensieTRHClass.timestamp <= date_to,
        )
    )

    result_df = DataFrame(session.execute(query).fetchall())

    if len(result_df.index) > 0:
        result_df.rename(columns={0: "Timestamp"}, inplace=True)
        
        result_df.set_index('Timestamp', inplace=True)

    return result_df