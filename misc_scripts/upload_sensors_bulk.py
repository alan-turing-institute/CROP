# Upload sensors from a CSV file into the database

# Usage:
#
# python upload_sensors_bulkpy --input_csv <full path to csv>

# Notes:
#   * If running from this directory, need to have '..' in your PYTHONPATH
#   * Need to set environment variables from .secrets/crop.sh

import os
import re
import argparse
from urllib import parse
from datetime import datetime
import pandas as pd
from sqlalchemy import and_
from __app__.crop.constants import (
    SQL_DBNAME,
    SQL_CONNECTION_STRING,
    CONST_ARANET_TRH_SENSOR_TYPE,
    CONST_ARANET_CO2_SENSOR_TYPE,
    CONST_ARANET_AIRVELOCITY_SENSOR_TYPE
)
from __app__.crop.db import connect_db, session_open, session_close
from __app__.crop.structure import TypeClass, SensorClass, LocationClass, SensorLocationClass
from __app__.crop.utils import query_result_to_array

TYPE_MAPPING = {
    "T/RH": CONST_ARANET_TRH_SENSOR_TYPE ,
    "CO2": CONST_ARANET_CO2_SENSOR_TYPE,
    "Air Velocity": CONST_ARANET_AIRVELOCITY_SENSOR_TYPE
}

def get_db_session():
    """
    Get an SQLAlchemy session object for destination database

    Returns:
    ========
    session: SQLAlchemy session object
    """
    database = SQL_DBNAME
    conn_string = SQL_CONNECTION_STRING
    success, log, engine = connect_db(conn_string, database)
    session = session_open(engine)
    return session


def parse_location(location):
    """
    Use a regex to decode location strings written as e.g. 10B3,
    or return generic locations for other regions of the farm.

    Parameters
    ==========
    location: str, column from sensor tracking CSV.
    """

    shelf_regex = re.compile("([\d]{1,2})([A-E])([1-4])")
    try:
        match = shelf_regex.search(location)
        if match:
            column, aisle, shelf = match.groups()
            return "Farm", aisle, int(column), int(shelf)
        elif location == "R&D":
            return "R&D", "A", 1, 1
        elif location == "Propagation":
            return "R&D", "A", 1, 1
        elif "Lobby 1" in location:
            return "Lobby1", "None", 1, 1
        else:
            print("Unknown location {}".format(location))
            return None, None, None, None
    except(TypeError):
        return None, None, None, None


def get_data_from_csv(input_filename):
    """
    Read a csv file into a dataframe, and modify slightly, selecting only useful rows,
    parsing the location.

    Parameters:
    ===========
    input_filename: str, full path to csv file

    Returns
    =======
    Pandas dataframe containing one row per sensor.
    """
    df = pd.read_csv(input_filename, dtype=str)
    df["Location"] = df.apply(lambda x: parse_location(x["Location"]), axis=1)
    #only keep rows with valid aranet code.
    df = df[~df["Code"].isna()]
    #only keep rows with an install date.
    df = df[~df["Install date"].isna()]
    # only keep T/RH, CO2, Air velocity
    df = df[df["Type"].isin(["T/RH", "Air Velocity", "CO2"])]
    df["Type"] = df.apply(lambda x: TYPE_MAPPING[x["Type"]], axis=1)
    return df


def get_existing_locations():
    """
    Not currently used.
    """
    session = get_db_session()
    query = session.query(
        LocationClass.zone,
        LocationClass.aisle,
        LocationClass.column,
        LocationClass.shelf
    )
    results = session.execute(query).fetchall()
    results_array = query_result_to_array(results)
    locations_df = pd.DataFrame(results_array)
    session_close(session)
    return locations_df


def get_existing_sensor_codes():
    """
    Query the sensor db table to get the aranet_code for all existing sensors.

    Returns
    =======
    sensors_df: two-column pandas dataframe, just containing aranet_code and aranet_pro_id variables.
    """
    session = get_db_session()
    query = session.query(
        SensorClass.aranet_code,
        SensorClass.aranet_pro_id
    )
    results = session.execute(query).fetchall()
    results_array = query_result_to_array(results)
    sensors_df = pd.DataFrame(results_array)
    session_close(session)
    return sensors_df


def get_sensor_type_id_mapping():
    """
    Query the sensor type table to map type_name to type_id

    Returns
    =======
    mapping: dict, keyed by sensor type name, with values of type_id
    """
    session = get_db_session()
    mapping = {}
    query = session.query(
        TypeClass.id,
        TypeClass.sensor_type
    )
    results = session.execute(query).fetchall()
    results_array = query_result_to_array(results)
    for result in results_array:
        mapping[result["sensor_type"]] = result["id"]
    session_close(session)
    return mapping


def get_location_id(session, location):
    """
    Find location_id, or if it doesn't exist, write a row in the DB and return
    the new id.

    Parameters
    ==========
    session: SQLAlchemy db session object
    location: tuple of (zone, aisle, column, shelf)

    Returns
    =======
    id: int
    """
    zone, aisle, column, shelf = location
    query = session.query(
        LocationClass.id,
        LocationClass.zone,
        LocationClass.aisle,
        LocationClass.column,
        LocationClass.shelf
    ).filter(
        and_(
            LocationClass.aisle == aisle,
            LocationClass.zone == zone,
            LocationClass.column == column,
            LocationClass.shelf == shelf
        )
    )
    results = session.execute(query).fetchall()
    results_array = query_result_to_array(results)
    if len(results_array) == 1:
        location_id = results_array[0]["id"]
        print("Found existing location with id {}".format(location_id))
        return location_id
    elif zone and aisle and column and shelf:
        location = LocationClass(zone=zone, aisle=aisle, column=column, shelf=shelf)
        session.add(location)
        session.commit()
        print("Added a new location at {} {} {} {}".format(zone, aisle, column, shelf))
        return location.id
    else:
        print("Some aspect of location unknown")
        return None


def write_sensor_location(session, sensor_id, location, installation_date):
    """
    write a row into sensorlocation column, including sensor_id and location_id

    Parameters
    ==========
    session: SQLAlchemy session object
    sensor_id: int, id of the newly added sensor in the SensorClass table
    location: tuple of (zone, aisle, column, shelf)
    installation_date: str, format "dd/mm/yy"

    Returns
    =======
    success: bool
    """
    location_id = get_location_id(session, location)
    if not location_id:
        return False
    sensor_location = SensorLocationClass()
    sensor_location.location_id = location_id
    sensor_location.sensor_id = sensor_id
    try:
        install_date = datetime.strptime(installation_date, "%d/%m/%Y")
    except(ValueError):
        install_date = datetime(2020,1,1,0,0)
    sensor_location.installation_date = install_date
    session.add(sensor_location)
    session.commit()
    print("Wrote sensor, location, installation date: {} {} {}".format(sensor_id, location_id, install_date))
    return True


def write_sensors(df_new, df_existing, type_id_mapping):
    """
    Copy non-overlapping rows from csv to destination database

    Parameters
    ==========
    new_df: pandas DataFrame, from input csv file
    existing_df: pandas DataFrame containing column of aranet code
    type_mapping: dict mapping sensor type names to sensor type IDs.

    Returns
    =======
    success: bool
    """
    success = True
    # remove rows with existing aranet_code
    df_new = df_new[~df_new["Code"].isin(df_existing["aranet_code"])]
    session = get_db_session()
    write_count = 0
    for idx, row in df_new.iterrows():
        sensor = SensorClass()
        sensor.aranet_code = row["Code"]
        sensor.aranet_pro_id = row["Aranet Pro ID"]
        sensor.serial_number = row["S/N"]
        sensor.type_id = type_id_mapping[row["Type"]]
        sensor.device_id = row["Aranet Pro ID"]
        sensor.name = row["Name"]
        session.add(sensor)
        session.commit()
        print("Writing {} {} {}".format(row["Type"], row["Code"], row["Aranet Pro ID"]))
        write_count += 1
        sensor_id = sensor.id
        success &= write_sensor_location(session, sensor_id, row["Location"], row["Install date"])

    session_close(session)
    print(f"Wrote {write_count} rows to database")
    return success




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="add sensor data from a csv file")
    parser.add_argument("--input_csv", type=str, help="path to a sensor tracking CSV file", required=True)
    args = parser.parse_args()
    input_df = get_data_from_csv(args.input_csv)
    sensor_type_id_mapping = get_sensor_type_id_mapping()
    existing_sensor_codes = get_existing_sensor_codes()
    success = write_sensors(input_df, existing_sensor_codes, sensor_type_id_mapping)
