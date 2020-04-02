"""
Python module to perform data ingress operations
for the Advanticsys sensors

"""

import pandas as pd

# from crop.db import create_database
from crop.constants import (
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
)


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

    df = pd.read_csv(file_path)

    return df


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
