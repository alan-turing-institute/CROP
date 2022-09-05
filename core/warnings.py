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
    WarningsClass,
    WarningTypesClass,
)

from .utils import (
    get_crop_db_session,
    filter_latest_sensor_location,
)

from .db import session_close

REPORTING_NO_DATA_NAME = "Sensor reporting no data"
REPORTING_LITTLE_DATA_NAME = "Sensor reporting little data"
REPORTING_SOME_DATA_NAME = "Sensor reporting only some data"
SHORT_DESCRIPTIONS = {
    REPORTING_NO_DATA_NAME: "Sensor number {} is not reporting data.",
    REPORTING_LITTLE_DATA_NAME: "Sensor number {} is reporting only a minority of data points.",
    REPORTING_SOME_DATA_NAME: "Sensor number {} is reporting only some data points.",
}


def write_warning_types(session):
    """Write to WarningTypesClass the rows defined by the above constants."""
    for name, short_description in SHORT_DESCRIPTIONS.items():
        warning_type = session.execute(
            select(WarningTypesClass).where(WarningTypesClass.name == name)
        ).first()
        if warning_type is None:
            # This row doesn't exist yet, so add it.
            warning_type = WarningTypesClass(
                name=name, short_description=short_description
            )
            session.add(warning_type)
        else:
            # This row exists, so update it.
            warning_type = warning_type[0]
            warning_type.name = name
    session.commit()


def get_warning_types(session):
    query = session.query(
        WarningTypesClass.id,
        WarningTypesClass.name,
        WarningTypesClass.short_description,
        WarningTypesClass.long_description,
    )
    results = pd.read_sql(query.statement, query.session.bind)
    results = results.set_index("name")
    return results


def get_aranet_sensors(session):
    query = session.query(SensorClass.id, LocationClass.zone).filter(
        and_(
            TypeClass.id == SensorClass.type_id,
            SensorLocationClass.location_id == LocationClass.id,
            SensorClass.id == SensorLocationClass.sensor_id,
            TypeClass.sensor_type == "Aranet T&RH",
            filter_latest_sensor_location(session),
        )
    )
    results = pd.read_sql(query.statement, query.session.bind)
    return results


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


# def too_cold_in_propagation_room(readings, location_zone):
#    """
#    Function to calculate if the temperature is too low in an area of the farm
#    readings: list of temperature values queried from the db
#    """
#    if len(readings) < 5:
#        print("Missing data in  %s - check sensor battery" % (location_zone))
#
#    else:
#        average_temp_ = [item[0] for _, item in enumerate(readings)]
#        average_temp = mean(average_temp_)
#
#        min_temp = 23
#        if average_temp < min_temp:
#            # issue warning
#            print("Temperature is low in %s, add heater" % (location_zone))
#            return average_temp
#        elif average_temp > 50:
#            print(average_temp)
#            return average_temp
#
#
# def too_humid_in_propagation_room(readings, location_zone):
#    """
#    Function to calculate if the humitidy is too high in an area of the farm
#    readings: list of humidity values queried from the db
#    """
#    if len(readings) < 5:
#        print("Missing data in  %s - check sensor battery" % (location_zone))
#    else:
#        average_hum_ = [item[1] for _, item in enumerate(readings)]
#        average_hum = mean(average_hum_)
#
#        max_hum = 80
#        if average_hum >= max_hum:
#            # issue warning
#            print("Too humid in  %s room - ventilate or dehumidify" % (location_zone))
#            return average_hum


# def upload_warnings(session, warning):
#    session = session_open(engine)
#    for idx, row in warning.iterrows():
#        data = WarningsClass(
#            type_id=type_id,
#            priority=prior,
#            log=warning_log,
#        )
#
#    session.add(data)


def create_and_upload_aranet_warnings(session, warning_types):
    check_period_hours = 24
    end_datetime = datetime.utcnow()
    start_datetime = end_datetime - timedelta(hours=check_period_hours)
    aranet_data = get_aranet_data(session, start_datetime, end_datetime)
    aranet_sensors = get_aranet_sensors(session)
    print(aranet_data)
    print(aranet_sensors)
    filter_out_last_hour = aranet_data["timestamp"] < end_datetime - timedelta(hours=1)
    counts_by_sensor = (
        aranet_data.loc[filter_out_last_hour, ["sensor_id", "timestamp"]]
        .groupby("sensor_id")
        .count()
    )

    priorities = {
        REPORTING_NO_DATA_NAME: 3,
        REPORTING_LITTLE_DATA_NAME: 2,
        REPORTING_SOME_DATA_NAME: 1,
    }
    for _, row in aranet_sensors.iterrows():
        sensor_id = row["id"]
        if sensor_id not in counts_by_sensor.index:
            reporting_status = REPORTING_NO_DATA_NAME
        else:
            count = counts_by_sensor.loc[sensor_id, "timestamp"]
            max_count = (check_period_hours - 1) * 6
            if count >= max_count:
                reporting_status = "full data"
            elif max_count // 2 < count < max_count:
                reporting_status = REPORTING_SOME_DATA_NAME
            else:
                reporting_status = REPORTING_LITTLE_DATA_NAME
        if reporting_status != "full data":
            session.add(
                WarningsClass(
                    sensor_id=int(sensor_id),
                    warning_type_id=int(warning_types.loc[reporting_status, "id"]),
                    priority=priorities[reporting_status],
                )
            )
    session.commit()


def create_and_upload_warnings():
    session, engine = get_crop_db_session(return_engine=True)
    if session is None:
        return False

    # Create the relevant tables if they don't yet exist
    try:
        WarningTypesClass.__table__.create(bind=engine)
    except ProgrammingError:
        pass
    try:
        WarningsClass.__table__.create(bind=engine)
    except ProgrammingError:
        pass

    try:
        write_warning_types(session)
        warning_types = get_warning_types(session)
        create_and_upload_aranet_warnings(session, warning_types)
    finally:
        session_close(session)
    return True


if __name__ == "__main__":
    create_and_upload_warnings()
