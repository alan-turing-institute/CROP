"""
Python module for misc sensor functions.
"""

from pandas import DataFrame
from sqlalchemy import and_

from __app__.crop.constants import (
    CONST_ARANET_TRH_SENSOR_TYPE,
    CONST_ARANET_CO2_SENSOR_TYPE,
    CONST_ARANET_AIRVELOCITY_SENSOR_TYPE,
)


from __app__.crop.structure import (
    TypeClass,
    SensorClass,
    ReadingsAranetTRHClass,
    ReadingsAranetCO2Class,
    ReadingsAranetAirVelocityClass,
    ReadingsWeatherClass,
)


def find_sensor_type_id(session, sensor_type):
    """
    Function to find sensor type id by name.

    Args:
        session: sqlalchemy active session object
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


def find_sensor_type_from_id(session, sensor_id):
    """
    Function to find the sensor type from its ID

    Args:
        session: sqlalchemy active session object
        sensor_id: sensor id
    Returns:
        success: bool,  sensor_type: str
    """
    query = session.query(TypeClass.sensor_type).filter(
        and_(
            SensorClass.id == sensor_id,
            TypeClass.id == SensorClass.type_id
        )
    )
    results = session.execute(query).fetchone()
    if results and len(results) == 1:
        success = True
        return success, results[0]
    else:
        print("Unknown sensor type")
        success = False
        return success, "Unknown"


def get_sensor_readings_db_timestamps(session, sensor_id, date_from, date_to):
    """
    Returns timestamps of sensor data for specific period of time as pandas data frame.
    Arguments:
        session: sqlalchemy active session object
        sensor_id: sensor id in the crop scheme (i.e. primary key in Sensor table).
        date_from: date range from
        date_to: date range to
    Returns:
        data_df: data frame containing timestamps of sensor data
    """
    # map sensor types to db tables (classes)
    mappings = {
        CONST_ARANET_TRH_SENSOR_TYPE : ReadingsAranetTRHClass,
        CONST_ARANET_CO2_SENSOR_TYPE : ReadingsAranetCO2Class,
        CONST_ARANET_AIRVELOCITY_SENSOR_TYPE : ReadingsAranetAirVelocityClass,
    }
    # get the sensor type
    success, sensor_type = find_sensor_type_from_id(session, sensor_id)
    if not success:
        return None
    if not sensor_type in mappings.keys():
        print("Sensor type {} not recognised".format(sensor_type))
        return None
    ReadingsClass = mappings[sensor_type]
    query = session.query(ReadingsClass.timestamp).filter(
        and_(
            ReadingsClass.sensor_id == sensor_id,
            ReadingsClass.timestamp >= date_from,
            ReadingsClass.timestamp <= date_to,
        )
    )

    result_df = DataFrame(session.execute(query).fetchall())

    if len(result_df.index) > 0:
        result_df.rename(columns={0: "Timestamp"}, inplace=True)
        result_df.set_index("Timestamp", inplace=True)

    return result_df


def get_db_weather_data(session, date_from, date_to):
    """
    Returns weather data for specific period of time as pandas data frame.

    Arguments:
        session: sqlalchemy active session object
        date_from: date range from
        date_to: date range to
    Returns:
        data_df: data frame containing sensor data for specific period of time
    """

    query = session.query(ReadingsWeatherClass.timestamp,).filter(
        and_(
            ReadingsWeatherClass.timestamp >= date_from,
            ReadingsWeatherClass.timestamp <= date_to,
        )
    )

    result_df = DataFrame(session.execute(query).fetchall())

    if len(result_df.index) > 0:
        result_df.set_index("timestamp", inplace=True)

    return result_df
