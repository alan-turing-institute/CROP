"""Create warnings highlighting issues with the data we have, or with farm
conditions.
"""
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import and_, select
from sqlalchemy.exc import ProgrammingError

from .structure import (
    TypeClass,
    SensorClass,
    SensorLocationClass,
    ReadingsAranetTRHClass,
    LocationClass,
    WarningClass,
    WarningTypeClass,
)
from .utils import (
    get_crop_db_session,
    filter_latest_sensor_location,
)
from .db import session_close

REPORTING_NO_DATA_NAME = "Sensor reporting no data"
REPORTING_LITTLE_DATA_NAME = "Sensor reporting little data"
REPORTING_SOME_DATA_NAME = "Sensor reporting only some data"
NO_LOCATION_NAME = "No location"
TOO_COLD_NAME = "Too cold"
TOO_HUMID_NAME = "Too humid"
SHORT_DESCRIPTIONS = {
    REPORTING_NO_DATA_NAME: "Sensor {sensor_name} is not reporting data.",
    REPORTING_LITTLE_DATA_NAME: "Sensor {sensor_name} is reporting only a minority of data points.",
    REPORTING_SOME_DATA_NAME: "Sensor {sensor_name} is reporting only some data points.",
    NO_LOCATION_NAME: "Sensor {sensor_name} has no location set.",
    TOO_COLD_NAME: "Too cold: Sensor {sensor_name} in {zone} was at {min_temp}°C at {time}.",
    TOO_HUMID_NAME: "Too humid: Sensor {sensor_name} in {zone} was at {max_humidity}% relative humidity at {time}.",
}
PRIORITIES = {
    REPORTING_NO_DATA_NAME: 3,
    REPORTING_LITTLE_DATA_NAME: 2,
    REPORTING_SOME_DATA_NAME: 1,
    NO_LOCATION_NAME: 1,
    TOO_COLD_NAME: 2,
    TOO_HUMID_NAME: 3,
}

PROPAGATION_MIN_TEMPERATURE = 23.0
PROPAGATION_MAX_HUMIDITY = 80.0


def write_warning_types(session):
    """Write to WarningTypeClass the rows defined by the above constants."""
    for name, short_description in SHORT_DESCRIPTIONS.items():
        warning_type = session.execute(
            select(WarningTypeClass).where(WarningTypeClass.name == name)
        ).first()
        if warning_type is None:
            # This row doesn't exist yet, so add it.
            warning_type = WarningTypeClass(
                name=name, short_description=short_description
            )
            session.add(warning_type)
        else:
            # This row exists, so update it.
            warning_type = warning_type[0]
            warning_type.short_description = short_description
    session.commit()


def get_warning_types(session):
    query = session.query(
        WarningTypeClass.id,
        WarningTypeClass.name,
        WarningTypeClass.short_description,
        WarningTypeClass.long_description,
    )
    results = pd.read_sql(query.statement, query.session.bind)
    results = results.set_index("name")
    return results


def get_sensors_without_locations(session):
    query = session.query(SensorClass.id).filter(
        SensorClass.id.not_in(session.query(SensorLocationClass.sensor_id))
    )
    sensors = pd.read_sql(query.statement, query.session.bind)
    return sensors


def get_aranet_sensors(session):
    query = session.query(SensorClass.id, LocationClass.zone).filter(
        and_(
            TypeClass.id == SensorClass.type_id,
            TypeClass.sensor_type == "Aranet T&RH",
            SensorClass.id == SensorLocationClass.sensor_id,
            SensorLocationClass.location_id == LocationClass.id,
            filter_latest_sensor_location(session),
        )
    )
    sensors = pd.read_sql(query.statement, query.session.bind)
    return sensors


def get_aranet_data(session, start_datetime, end_datetime):
    query = session.query(
        ReadingsAranetTRHClass.sensor_id,
        ReadingsAranetTRHClass.humidity,
        ReadingsAranetTRHClass.temperature,
        ReadingsAranetTRHClass.timestamp,
    ).filter(
        and_(
            ReadingsAranetTRHClass.timestamp >= start_datetime,
            ReadingsAranetTRHClass.timestamp < end_datetime,
        )
    )
    results = pd.read_sql(query.statement, query.session.bind)
    return results


def warn_missing_locations(session, warning_types):
    """Create warnings for sensors that have no location set."""
    sensors = get_sensors_without_locations(session)
    for _, row in sensors.iterrows():
        warning = WarningClass(
            sensor_id=int(row["id"]),
            warning_type_id=int(warning_types.loc[NO_LOCATION_NAME, "id"]),
            priority=PRIORITIES[NO_LOCATION_NAME],
        )
        session.add(warning)
    session.commit()


# TODO Make this general for any zone, have limits be in a DB table or dictionary.
def warn_propagation_conditions(session, warning_types, data, sensors):
    """Create warnings if T&RH conditions in Propagation are outside allowed bounds."""
    sensors = sensors.set_index("id")
    # Drop sensors for which we do not know their location. Copy to be able to mutate
    # the DataFrame later.
    data = data.loc[data["sensor_id"].isin(sensors.index), :].copy()
    # Filter out everything outside of the selected zone.
    data["zone"] = data["sensor_id"].apply(
        lambda sensor_id: sensors.loc[sensor_id, "zone"]
    )
    df = data[data["zone"] == "Propagation"]

    minmax_values = (
        df.loc[:, ["sensor_id", "temperature", "humidity"]]
        .groupby("sensor_id")
        .agg(("min", "max"))
    )
    for sensor_id, row in minmax_values.iterrows():
        min_temp = row["temperature"]["min"]
        max_humidity = row["humidity"]["max"]
        if min_temp < PROPAGATION_MIN_TEMPERATURE:
            # Find the latest time this value occurred.
            time = df.loc[
                (df["sensor_id"] == sensor_id) & (df["temperature"] == min_temp),
                "timestamp",
            ].max()
            warning = WarningClass(
                sensor_id=int(sensor_id),
                warning_type_id=int(warning_types.loc[TOO_COLD_NAME, "id"]),
                priority=PRIORITIES[TOO_COLD_NAME],
                time=time,
                other_data={"min_temp": min_temp, "zone": "Propagation"},
            )
            session.add(warning)
        if max_humidity < PROPAGATION_MAX_HUMIDITY:
            # Find the latest time this value occurred.
            time = df.loc[
                (df["sensor_id"] == sensor_id) & (df["humidity"] == max_humidity),
                "timestamp",
            ].max()
            warning = WarningClass(
                sensor_id=int(sensor_id),
                warning_type_id=int(warning_types.loc[TOO_HUMID_NAME, "id"]),
                priority=PRIORITIES[TOO_HUMID_NAME],
                time=time,
                other_data={"max_humidity": max_humidity, "zone": "Propagation"},
            )
            session.add(warning)
    session.commit()


def warn_missing_aranet_data(
    session, warning_types, data, sensors, data_time_period_hours
):
    """Create warnings if Aranet sensors are missing some or all data from the last
    data_time_period_hours.
    """
    filter_out_last_hour = data["timestamp"] < datetime.utcnow() - timedelta(hours=1)
    counts_by_sensor = (
        data.loc[filter_out_last_hour, ["sensor_id", "timestamp"]]
        .groupby("sensor_id")
        .count()
    )

    for _, row in sensors.iterrows():
        sensor_id = row["id"]
        if sensor_id not in counts_by_sensor.index:
            reporting_status = REPORTING_NO_DATA_NAME
        else:
            count = counts_by_sensor.loc[sensor_id, "timestamp"]
            max_count = (data_time_period_hours - 1) * 6
            if count >= max_count:
                reporting_status = "full data"
            elif max_count // 2 < count < max_count:
                reporting_status = REPORTING_SOME_DATA_NAME
            else:
                reporting_status = REPORTING_LITTLE_DATA_NAME
        if reporting_status != "full data":
            warning = WarningClass(
                sensor_id=int(sensor_id),
                warning_type_id=int(warning_types.loc[reporting_status, "id"]),
                priority=PRIORITIES[reporting_status],
            )
            session.add(warning)
    session.commit()


def warn_aranet(session, warning_types):
    """Create various warnings related to Aranet sensors."""
    data_time_period_hours = 24
    end_datetime = datetime.utcnow()
    start_datetime = end_datetime - timedelta(hours=data_time_period_hours)
    data = get_aranet_data(session, start_datetime, end_datetime)
    sensors = get_aranet_sensors(session)

    warn_missing_aranet_data(
        session, warning_types, data, sensors, data_time_period_hours
    )
    warn_propagation_conditions(session, warning_types, data, sensors)


def create_and_upload_warnings():
    """The main entry point into this module. The function app calls this."""
    session, engine = get_crop_db_session(return_engine=True)
    if session is None:
        return False

    # Create the relevant tables if they don't yet exist
    try:
        WarningTypeClass.__table__.create(bind=engine)
    except ProgrammingError:
        pass
    try:
        WarningClass.__table__.create(bind=engine)
    except ProgrammingError:
        pass

    try:
        write_warning_types(session)
        warning_types = get_warning_types(session)
        warn_missing_locations(session, warning_types)
        warn_aranet(session, warning_types)
    finally:
        session_close(session)


if __name__ == "__main__":
    create_and_upload_warnings()
