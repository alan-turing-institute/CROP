import time
from datetime import datetime, timedelta

import pandas as pd
from numpy import mean

from sqlalchemy import and_

from __app__.crop.structure import (
    TypeClass,
    SensorClass,
    SensorLocationClass,
    ReadingsZensieTRHClass,
    LocationClass,
)

from __app__.crop.utils import query_result_to_array

from __app__.crop.constants import (
    CONST_ADVANTICSYS,
    SQL_ENGINE,
    SQL_DBNAME,
    SQL_HOST,
    SQL_CONNECTION_STRING_CROP,
)

from __app__.crop.db import connect_db, session_open, session_close

db_name = "app_db"
CONNECTION_STRING = "postgresql://cropdbadmin@cropapptestsqlserver:QhXZ7qZddDr224Mc2P4k@cropapptestsqlserver.postgres.database.azure.com:5432"

# Try to connect to a database that exists
success, log, engine = connect_db(CONNECTION_STRING, SQL_DBNAME)


def db_query_tmpr_day_zenzie(session, location_zone, date_range):

    """
    Function to query temperature readings from the Crop dabase's
    zenzie sensors located in the propagation area of the farm
    location_zone (str): the zone of the farm to query
    """
    query = session.query(
        ReadingsZensieTRHClass.temperature,
        ReadingsZensieTRHClass.humidity,
        # ReadingsZensieTRHClass.sensor_id,
    ).filter(
        and_(
            LocationClass.zone == location_zone,
            SensorLocationClass.location_id == LocationClass.id,  # propagation location
            # SensorLocationClass.location_id == location_id,
            ReadingsZensieTRHClass.sensor_id == SensorLocationClass.sensor_id,
            ReadingsZensieTRHClass.time_created >= date_range,
        )
    )
    readings = session.execute(query).fetchall()
    # TODO: query_result_to_array(readings))
    return readings


def too_cold_in_propagation_room(readings, location_zone):
    """
    Function to calculate if the temperature is too low in an area of the farm
    readings: list of temperature values queried from the db
    """
    if len(readings) < 5:
        print("Missing data in  %s - check sensor battery" % (location_zone))

    else:
        average_temp_ = []
        for i in range(len(readings)):
            average_temp_.append(readings[i][0])
        average_temp = mean(average_temp_)

        min_temp = 23
        if average_temp < min_temp:
            # issue warning
            print("Temperature is low in %s, add heater" % (location_zone))
            return average_temp
        elif average_temp > 50:
            print(average_temp)
            return average_temp


def too_humid_in_propagation_room(readings, location_zone):
    """
    Function to calculate if the humitidy is too high in an area of the farm
    readings: list of humidity values queried from the db
    """
    if len(readings) < 5:
        print("Missing data in  %s - check sensor battery" % (location_zone))
    else:
        average_hum_ = []
        for i in range(len(readings)):
            average_hum_.append(readings[i][1])
        average_hum = mean(average_hum_)

        max_hum = 80
        if average_hum >= max_hum:
            # issue warning
            print("Too humid in  %s room - ventilate or dehumidify" % (location_zone))
            return average_hum


def check_issues_in_farm(session):

    start_date = datetime.now() - timedelta(hours=24)
    propagation_zone = "Propagation"

    readings = db_query_tmpr_day_zenzie(session, propagation_zone, start_date)

    too_cold_in_propagation_room(readings, propagation_zone)

    too_humid_in_propagation_room(readings, propagation_zone)


def issue_warnings():
    None


def upload_warning_db(session, warning):
    None


if __name__ == "__main__":
    session = session_open(engine)

    check_issues_in_farm(session)

    session_close(session)