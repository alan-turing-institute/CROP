"""Create warnings highlighting issues with the data we have, or with farm
conditions.
"""
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import and_, select
from sqlalchemy.exc import ProgrammingError

from . import queries
from .structure import (
    TypeClass,
    SensorClass,
    SensorLocationClass,
    ReadingsAranetTRHClass,
    ReadingsWeatherClass,
    LocationClass,
    WarningClass,
    WarningTypeClass,
)
from .utils import get_crop_db_session
from .db import session_close

# TODO Can we avoid having these constants? If not, should they be in core.constants?
REPORTING_NO_DATA_NAME = "Sensor reporting no data"
REPORTING_LITTLE_DATA_NAME = "Sensor reporting little data"
REPORTING_SOME_DATA_NAME = "Sensor reporting only some data"
NO_LOCATION_NAME = "No location"
TOO_COLD_NAME = "Too cold"
TOO_HUMID_NAME = "Too humid"
OUTSIDE_TOO_HUMID_NAME = "Outside too humid"
SHORT_DESCRIPTIONS = {
    REPORTING_NO_DATA_NAME: "Sensor {sensor_name} is not reporting data.",
    REPORTING_LITTLE_DATA_NAME: "Sensor {sensor_name} is reporting only a minority of data points.",
    REPORTING_SOME_DATA_NAME: "Sensor {sensor_name} is reporting only some data points.",
    NO_LOCATION_NAME: "Sensor {sensor_name} has no location set.",
    TOO_COLD_NAME: "Too cold: Sensor {sensor_name} in {zone} was at {min_temperature}°C at {time}.",
    TOO_HUMID_NAME: "Too humid: Sensor {sensor_name} in {zone} was at {max_humidity}% relative humidity at {time}.",
    OUTSIDE_TOO_HUMID_NAME: "Relative humidity outside ({outside_rh}%) is higher than inside ({inside_rh}%).",
}
PRIORITIES = {
    REPORTING_NO_DATA_NAME: 3,
    REPORTING_LITTLE_DATA_NAME: 2,
    REPORTING_SOME_DATA_NAME: 1,
    NO_LOCATION_NAME: 1,
    TOO_COLD_NAME: 3,
    TOO_HUMID_NAME: 3,
    OUTSIDE_TOO_HUMID_NAME: 4,
}
CATEGORIES = {
    REPORTING_NO_DATA_NAME: "Missing data",
    REPORTING_LITTLE_DATA_NAME: "Missing data",
    REPORTING_SOME_DATA_NAME: "Missing data",
    NO_LOCATION_NAME: "Missing data",
    TOO_COLD_NAME: "Farm conditions",
    TOO_HUMID_NAME: "Farm conditions",
    OUTSIDE_TOO_HUMID_NAME: "Farm conditions",
}

# TODO Should this rather be in the database?
ZONE_CONDITION_BOUNDS = {
    "Propagation": [
        # For each element in this list, if the `bound_type` extremal value (min or max)
        # of `metric` compares to `bound_value` with `comparison_operator`, then create
        # a warning of `warning_type` in the warn_conditions_zone function. E.g. this
        # first entry says that if the min temperature reached by any sensor in
        # Propagation was less than 23.0, we should create a TOO_COLD warning.
        {
            "metric": "temperature",
            "bound_type": "min",
            "comparison_operator": np.less,
            "bound_value": 23.0,
            "warning_type": TOO_COLD_NAME,
        },
        {
            "metric": "humidity",
            "bound_type": "max",
            "comparison_operator": np.greater,
            "bound_value": 80.0,
            "warning_type": TOO_HUMID_NAME,
        },
    ]
}


def write_warning_types(session):
    """Write to WarningTypeClass the rows defined by the above constants."""
    for name, short_description in SHORT_DESCRIPTIONS.items():
        warning_type = session.execute(
            select(WarningTypeClass).where(WarningTypeClass.name == name)
        ).first()
        if warning_type is None:
            # This row doesn't exist yet, so add it.
            warning_type = WarningTypeClass(
                name=name,
                short_description=short_description,
                category=CATEGORIES[name],
            )
            session.add(warning_type)
        else:
            # This row exists, so update it.
            warning_type = warning_type[0]
            warning_type.short_description = short_description
            warning_type.category = CATEGORIES[name]
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
    locations_query = queries.latest_sensor_locations(session).subquery()
    query = session.query(SensorClass.id, LocationClass.zone).filter(
        and_(
            TypeClass.id == SensorClass.type_id,
            TypeClass.sensor_type == "Aranet T&RH",
            SensorClass.id == locations_query.c.sensor_id,
            locations_query.c.location_id == LocationClass.id,
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


def get_weather_data(session, start_datetime, end_datetime):
    query = session.query(
        ReadingsWeatherClass.relative_humidity,
        ReadingsWeatherClass.temperature,
        ReadingsWeatherClass.timestamp,
    ).filter(
        and_(
            ReadingsWeatherClass.timestamp >= start_datetime,
            ReadingsWeatherClass.timestamp < end_datetime,
        )
    )
    results = pd.read_sql(query.statement, query.session.bind)
    return results


def warn_missing_locations(session, warning_types):
    """Create warnings for sensors that have no location set."""
    sensors = get_sensors_without_locations(session)
    for _, row in sensors.iterrows():
        # The conversions to int seem necessary because SQLAlchemy can't handle
        # numpy.int64.
        warning_type_id = int(warning_types.loc[NO_LOCATION_NAME, "id"])
        warning = WarningClass(
            sensor_id=int(row["id"]),
            warning_type_id=warning_type_id,
            priority=PRIORITIES[NO_LOCATION_NAME],
        )
        session.add(warning)
    session.commit()


def warn_zone_trh_conditions(session, warning_types, data, zone):
    """Create warnings if T&RH conditions in `zone` are outside allowed bounds."""
    df = data[data["zone"] == zone]
    extremal_values = (
        df.loc[:, ["sensor_id", "temperature", "humidity"]]
        .groupby("sensor_id")
        .agg(("min", "max"))
    )
    for sensor_id, row in extremal_values.iterrows():
        for bound in ZONE_CONDITION_BOUNDS[zone]:
            # See comment at the definition of ZONE_CONDITION_BOUNDS for an explanation
            # of this part.
            metric, bound_type, bound_value, comparison_operator, warning_type = (
                bound["metric"],
                bound["bound_type"],
                bound["bound_value"],
                bound["comparison_operator"],
                bound["warning_type"],
            )
            extremal_value = row[metric][bound_type]
            if comparison_operator(extremal_value, bound_value):
                # Find the latest time this value occurred.
                time = df.loc[
                    (df["sensor_id"] == sensor_id) & (df[metric] == extremal_value),
                    "timestamp",
                ].max()
                warning_type_id = int(warning_types.loc[warning_type, "id"])
                bound_name = f"{bound_type}_{metric}"
                warning = WarningClass(
                    sensor_id=sensor_id,
                    warning_type_id=warning_type_id,
                    priority=PRIORITIES[warning_type],
                    time=time,
                    other_data={bound_name: extremal_value, "zone": zone},
                )
                session.add(warning)
    session.commit()


def warn_trh_conditions(session, warning_types, data, sensors):
    """Create warnings if T&RH conditions are outside allowed bounds."""
    sensors = sensors.set_index("id")
    # Drop sensors for which we do not know their location. Copy to be able to mutate
    # the DataFrame later.
    data = data.loc[data["sensor_id"].isin(sensors.index), :].copy()
    data["zone"] = data["sensor_id"].apply(
        lambda sensor_id: sensors.loc[sensor_id, "zone"]
    )
    for zone in ZONE_CONDITION_BOUNDS:
        warn_zone_trh_conditions(session, warning_types, data, zone)


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

    # Note that this loop doesn't include sensors that don't have a location set, since
    # they weren't included in the query that produced `sensors`.
    for _, row in sensors.iterrows():
        # Skip sensors explicitly marked as not being in use.
        if row["zone"] in ("Not in use", "Retired"):
            continue
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
            warning_type_id = int(warning_types.loc[reporting_status, "id"])
            warning = WarningClass(
                sensor_id=sensor_id,
                warning_type_id=warning_type_id,
                priority=PRIORITIES[reporting_status],
            )
            session.add(warning)
    session.commit()


def warn_external_conditions(session, warning_types, data, weather_data):
    """Warn if outside temperature or relative humidity are somehow problematic."""
    # TODO Is relative humidity really the right thing to compare? Wouldn't absolute
    # humidity be more relevant for this?
    weather_last_idx = weather_data["timestamp"].idxmax()
    latest_outside_rh = weather_data.loc[weather_last_idx, "relative_humidity"]
    now = datetime.utcnow()
    last_two_hours_data = data[data["timestamp"] >= now - timedelta(hours=2)]
    if len(last_two_hours_data) == 0:
        return
    latest_inside_rh = last_two_hours_data["humidity"].mean()
    if latest_outside_rh > latest_inside_rh:
        warning_type_id = int(warning_types.loc[OUTSIDE_TOO_HUMID_NAME, "id"])
        warning = WarningClass(
            warning_type_id=warning_type_id,
            priority=PRIORITIES[OUTSIDE_TOO_HUMID_NAME],
            other_data={"outside_rh": latest_outside_rh, "inside_rh": latest_inside_rh},
        )
        session.add(warning)
        session.commit()


def warn_aranet(session, warning_types):
    """Create various warnings related to Aranet sensors."""
    data_time_period_hours = 24
    end_datetime = datetime.utcnow()
    start_datetime = end_datetime - timedelta(hours=data_time_period_hours)
    data = get_aranet_data(session, start_datetime, end_datetime)
    weather_data = get_weather_data(session, start_datetime, end_datetime)
    sensors = get_aranet_sensors(session)

    warn_missing_aranet_data(
        session, warning_types, data, sensors, data_time_period_hours
    )
    warn_trh_conditions(session, warning_types, data, sensors)
    warn_external_conditions(session, warning_types, data, weather_data)


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
