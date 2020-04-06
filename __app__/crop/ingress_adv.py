"""
Python module to perform data ingress operations
for the Advanticsys sensors

"""

import pandas as pd

# from crop.db import create_database
from __app__.crop.constants import (
    CONST_ADVANTICSYS_COL_LIST,
    CONST_ADVANTICSYS_COL_TIMESTAMP,
    CONST_ADVANTICSYS_COL_MODBUSID,
    CONST_ADVANTICSYS_COL_TEMPERATURE,
    CONST_ADVANTICSYS_COL_HUMIDITY,
    CONST_ADVANTICSYS_COL_CO2LEVEL,
    ERR_IMPORT_ERROR_1,
    ERR_IMPORT_ERROR_2,
    ERR_IMPORT_ERROR_3,
    ERR_IMPORT_ERROR_4,
    ERR_IMPORT_ERROR_5,
    CONST_ADVANTICSYS_TIMESTAMP_MIN,
    CONST_ADVANTICSYS_TIMESTAMP_MAX,
    CONST_ADVANTICSYS_MODBUSID_MIN,
    CONST_ADVANTICSYS_MODBUSID_MAX,
    CONST_ADVANTICSYS_TEMPERATURE_MIN,
    CONST_ADVANTICSYS_TEMPERATURE_MAX,
    CONST_ADVANTICSYS_HUMIDITY_MIN,
    CONST_ADVANTICSYS_HUMIDITY_MAX,
    CONST_ADVANTICSYS_CO2LEVEL_MIN,
    CONST_ADVANTICSYS_CO2LEVEL_MAX,
    CONST_ADVANTICSYS,
)


from __app__.crop.structure import SensorClass, TypeClass, ReadingsAdvanticsysClass


def advanticsys_import(file_path):
    """
    Reads in advanticsys csv file as pandas data frame and performs checks

    Args:
        file_path - full path to an advanticsys csv file
    Returns:
        success - status
        log - error message
        advanticsys_df - pandas dataframe representing advanticsys data file,
        returns None if data is invalid
    """

    advanticsys_raw_df = advanticsys_read_csv(file_path)

    return advanticsys_df_checks(advanticsys_raw_df)


def advanticsys_df_checks(advanticsys_raw_df):
    """
    Args
    Return
    """
    # Checks if df exists
    if not isinstance(advanticsys_raw_df, pd.DataFrame):
        return False, "Not a pandas dataframe", None

    # Checks if df is empty
    if advanticsys_raw_df.empty:
        return False, "Dataframe empty", None

    # Checks structure
    success, log = advanticsys_check_structure(advanticsys_raw_df)
    if not success:
        return success, log, None

    # converts data and uses only columns from CONST_ADVANTICSYS_COL_LIST
    success, log, advanticsys_df = advanticsys_convert(advanticsys_raw_df)
    if not success:
        return success, log, None

    # Checks for validity
    success, log = advanticsys_df_validity(advanticsys_df)
    if not success:
        return success, log, None

    return success, log, advanticsys_df


def advanticsys_read_csv(file_path):
    """
    Reads in advanticsys csv file as pandas data frame.

    Args:
        file_path - full path to an advanticsys csv file
    Returns:
        df - pandas dataframe representing advanticsys data file
    """

    return pd.read_csv(file_path)


def advanticsys_check_structure(advanticsys_df):
    """
    Checks if advanticsys dataframe has expected structure

    Args:
        advanticsys_df - pandas dataframe representing advanticsys data file
    Returns:
        True/False depending on whether the dataframe has the correct structure
        Error message
    """

    # Check if all the nessecary columns are present in the dataframe
    for advanticsys_column in CONST_ADVANTICSYS_COL_LIST:
        if not advanticsys_column in advanticsys_df.columns:
            return False, ERR_IMPORT_ERROR_1

    return True, None


def advanticsys_convert(advanticsys_raw_df):
    """
    Prepares Adavantix dataframe to be imported to database by selecting only neccessary columns
        and converting to correct data types.

    Args:
        advanticsys_raw_df - pandas dataframe representing advanticsys data file
    Returns:
        success - status
        log - error message
        advanticsys_df - converted pandas dataframe
    """

    success = True
    log = None

    try:
        advanticsys_df = advanticsys_raw_df[CONST_ADVANTICSYS_COL_LIST]
    except:
        success = False
        log = ERR_IMPORT_ERROR_1 + ": " + ",".join(CONST_ADVANTICSYS_COL_LIST)
        advanticsys_df = None
        return success, log, advanticsys_df

    # convert to expected types
    try:
        advanticsys_df[CONST_ADVANTICSYS_COL_TIMESTAMP] = pd.to_datetime(
            advanticsys_df[CONST_ADVANTICSYS_COL_TIMESTAMP],
            format="%Y-%m-%dT%H:%M:%S.%f",
        )
        advanticsys_df[CONST_ADVANTICSYS_COL_MODBUSID] = advanticsys_df[
            CONST_ADVANTICSYS_COL_MODBUSID
        ].astype("int16")
        advanticsys_df[CONST_ADVANTICSYS_COL_TEMPERATURE] = advanticsys_df[
            CONST_ADVANTICSYS_COL_TEMPERATURE
        ].astype("float64")
        advanticsys_df[CONST_ADVANTICSYS_COL_HUMIDITY] = advanticsys_df[
            CONST_ADVANTICSYS_COL_HUMIDITY
        ].astype("float64")
        advanticsys_df[CONST_ADVANTICSYS_COL_CO2LEVEL] = advanticsys_df[
            CONST_ADVANTICSYS_COL_CO2LEVEL
        ].astype("float64")
    except:
        success = False
        log = ERR_IMPORT_ERROR_2
        advanticsys_df = None
        return success, log, advanticsys_df

    # check for missing values
    if advanticsys_df.isnull().values.any():
        success = False
        log = ERR_IMPORT_ERROR_3
        advanticsys_df = None
        return success, log, advanticsys_df

    return success, log, advanticsys_df


def advanticsys_df_validity(advanticsys_df):
    """
    Checks if advanticsys dataframe has expected structure

    Args:
        advanticsys_df - pandas dataframe representing advanticsys data file
    Returns:
        True/False depending on whether the dataframe has the correct stricture
        Error message
    """

    success = True
    log = ""

    # Checking for duplicates
    duplicates = advanticsys_df[advanticsys_df.duplicated()]
    if len(duplicates) > 0:
        success = False
        log = (
            ERR_IMPORT_ERROR_4
            + ". Check the following entries: "
            + str(list(duplicates.index))
        )
    if not success:
        return success, log

    col_names = [
        CONST_ADVANTICSYS_COL_TIMESTAMP,
        CONST_ADVANTICSYS_COL_MODBUSID,
        CONST_ADVANTICSYS_COL_TEMPERATURE,
        CONST_ADVANTICSYS_COL_HUMIDITY,
        CONST_ADVANTICSYS_COL_CO2LEVEL,
    ]
    col_mins = [
        CONST_ADVANTICSYS_TIMESTAMP_MIN,
        CONST_ADVANTICSYS_MODBUSID_MIN,
        CONST_ADVANTICSYS_TEMPERATURE_MIN,
        CONST_ADVANTICSYS_HUMIDITY_MIN,
        CONST_ADVANTICSYS_CO2LEVEL_MIN,
    ]
    col_maxs = [
        CONST_ADVANTICSYS_TIMESTAMP_MAX,
        CONST_ADVANTICSYS_MODBUSID_MAX,
        CONST_ADVANTICSYS_TEMPERATURE_MAX,
        CONST_ADVANTICSYS_HUMIDITY_MAX,
        CONST_ADVANTICSYS_CO2LEVEL_MAX,
    ]

    # Check every column
    for col_name, col_min, col_max in zip(col_names, col_mins, col_maxs):
        success, log = advanticsys_df_check_range(
            advanticsys_df, col_name, col_min, col_max
        )
        if not success:
            return success, log

    return success, log


def advanticsys_df_check_range(advanticsys_df, col_name, col_min, col_max):
    """
    Checks if value in a dataframe for a specific column are within a range.
    If not creates an error message.

    Args:
        advanticsys_df - pandas dataframe representing advanticsys data file
        col_name - column name
        col_min - minimum value
        col_max - maximum value
    Returns:
        success - status
        log - error message
    """

    success = True
    log = ""

    out_of_range_df = advanticsys_df[
        (advanticsys_df[col_name] < col_min) | (advanticsys_df[col_name] > col_max)
    ]

    if len(out_of_range_df) > 0:
        success = False
        log = (
            ERR_IMPORT_ERROR_5
            + " <"
            + col_name
            + "> out of range (min = %f, max = %f)" % (col_min, col_max)
            + " Entries: "
            + str(list(out_of_range_df.index))
        )

    return success, log


def insert_advanticsys_data(session, adv_df):
    """
    The function will take the prepared advanticsys data frame from the ingress module
    and find sensor id with respect to modbusid and sensor type and insert data into the db.
    -session: an open sqlalchemy session
    -adv_df: dataframe containing a checked advanticsys df
    -cnt_dupl: counts duplicate values
    """

    result = True
    log = ""
    cnt_dupl = 0

    # Gets the the assigned int id of the "Advanticsys" type
    try:
        adv_type_id = (
            session.query(TypeClass)
            .filter(TypeClass.sensor_type == CONST_ADVANTICSYS)
            .first()
            .id
        )
    except:
        result = False
        log = "Sensor type {} was not found.".format(CONST_ADVANTICSYS)
        return result, log

    # Gets the sensor_id of the sensor with type=advanticsys and device_id=modbusid
    for _, row in adv_df.iterrows():

        adv_device_id = row[CONST_ADVANTICSYS_COL_MODBUSID]
        adv_timestamp = row[CONST_ADVANTICSYS_COL_TIMESTAMP]

        try:
            adv_sensor_id = (
                session.query(SensorClass)
                .filter(SensorClass.device_id == str(adv_device_id))
                .filter(SensorClass.type_id == adv_type_id)
                .first()
                .id
            )
        except:
            adv_sensor_id = -1
            result = False
            log = "{} sensor with {} = {} was not found.".format(
                CONST_ADVANTICSYS, CONST_ADVANTICSYS_COL_MODBUSID, str(adv_device_id)
            )
            break

        # check if data entry already exists
        if adv_sensor_id != -1:

            found = False

            query_result = (
                session.query(ReadingsAdvanticsysClass)
                .filter(ReadingsAdvanticsysClass.sensor_id == adv_sensor_id)
                .filter(ReadingsAdvanticsysClass.timestamp == adv_timestamp)
                .first()
            )

            if query_result is not None:
                found = True

            try:
                if not found:
                    data = ReadingsAdvanticsysClass(
                        sensor_id=adv_sensor_id,
                        timestamp=adv_timestamp,
                        temperature=row[CONST_ADVANTICSYS_COL_TEMPERATURE],
                        humidity=row[CONST_ADVANTICSYS_COL_HUMIDITY],
                        co2=row[CONST_ADVANTICSYS_COL_CO2LEVEL],
                    )
                    session.add(data)

                else:
                    cnt_dupl += 1
            except:
                result = False
                log = "Cannot insert new data to database"

    if cnt_dupl != 0:
        result = False
        log = "Cannot insert {} duplicate values".format(cnt_dupl)

    return result, log
