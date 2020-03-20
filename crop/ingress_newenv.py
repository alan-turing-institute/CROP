"""
Python module to perform data ingress operations
for the New Environmental sensors

"""
import os
import pandas as pd

from crop.constants import (
    CONST_TEST_DIR_DATA,
    CONST_NEW_ENV_FOLDER,
    CONST_NEW_ENV_TEST_1,
    ERR_IMPORT_ERROR_1,
    CONST_NEW_ENV_COL_LIST
)

file_path = os.path.join(
    CONST_TEST_DIR_DATA, CONST_NEW_ENV_FOLDER, CONST_NEW_ENV_TEST_1
)

def newenv_import(file_path):
    """
    Reads in the New Environemntal csv file as pandas data frame and performs checks

    Args:
        file_path - full path to an new_env csv file
    Returns:
        success - status
        log - error message
        new_env_df - pandas dataframe representing new_env data file,
        returns None if data is invalid
    """

    new_env_raw_df = new_env_read_csv(file_path)
    print (new_env_raw_df)
    return new_env_df_checks(new_env_raw_df)


def new_env_df_checks(new_env_raw_df):
    """
    Args
    Return
    """
    # Checks if df exists
    if not isinstance(new_env_raw_df, pd.DataFrame):
        return False, "Not a pandas dataframe", None

    # Checks if df is empty
    if new_env_raw_df.empty:
        return False, "Dataframe empty", None

    # Checks structure
    success, log = new_env_check_structure(new_env_raw_df)
    if not success:
        return success, log, None

    new_env_df = new_env_raw_df
    # converts data and uses only columns from CONST_NEW_ENV_COL_LIST
    success, log, new_env_df = new_env_convert(new_env_raw_df)
    if not success:
        return success, log, None

    # # Checks for validity
    # success, log = advantix_df_validity(advantix_df)
    # if not success:
    #     return success, log, None

    return success, log, new_env_df

def new_env_read_csv(file_path):
    """
    Reads in new environmental sensor csv file as pandas data frame.

    Args:
        file_path - full path to an new environmental sensor csv file
    Returns:
        df - pandas dataframe representing new environmental sensor data file
    """

    df = pd.read_csv(file_path)

    return df

def new_env_check_structure(new_env_df):
    """
    Checks if new environmental sensor dataframe has expected structure

    Args:
        new_env_df - pandas dataframe representing new environmental sensor data file
    Returns:
        True/False depending on whether the dataframe has the correct structure
        Error message
    """

    # Check if all the nessecary columns are present in the dataframe
    for new_env_column in CONST_NEW_ENV_COL_LIST:
        if not new_env_column in new_env_df.columns:
            return False, ERR_IMPORT_ERROR_1

    return True, None

def new_env_convert(new_env_raw_df):
    """
    Prepares New Enviromental dataframe to be imported to database by selecting only neccessary columns
        and converting to correct data types.

    Args:
        new_env_raw_df - pandas dataframe representing new_env data file
    Returns:
        success - status
        log - error message
        new_env_df - converted pandas dataframe
    """

    success = True
    log = None

    try:
        new_env_df = new_env_raw_df[CONST_NEW_ENV_COL_LIST]
    except:
        success = False
        log = ERR_IMPORT_ERROR_1 + ": " + ",".join(CONST_NEW_ENV_COL_LIST)
        new_env_df = None
        return success, log, new_env_df

    # convert to expected types
    try:
        new_env_df[CONST_NEW_ENV_COL_TIMESTAMP] = pd.to_datetime(
            new_env_df[CONST_NEW_ENV_COL_TIMESTAMP], format="%Y-%m-%dT%H:%M:%S.%f"
        )
        new_env_df[CONST_NEW_ENV_COL_DEVICE] = new_env_df[
            CONST_NEW_ENV_COL_DEVICE
        ].astype("int16")
        new_env_df[CONST_NEW_ENV_COL_TEMPERATURE] = new_env_df[
            CONST_NEW_ENV_COL_TEMPERATURE
        ].astype("float64")
        new_env_df[CONST_NEW_ENV_COL_HUMIDITY] = new_env_df[
            CONST_NEW_ENV_COL_HUMIDITY
        ].astype("float64")
        new_env_df[CONST_NEW_ENV_COL_CO2LEVEL] = new_env_df[
            CONST_NEW_ENV_COL_CO2LEVEL
        ].astype("float64")
    except:
        success = False
        log = ERR_IMPORT_ERROR_2
        new_env_df = None
        return success, log, new_env_df

    # check for missing values
    if new_env_df.isnull().values.any():
        success = False
        log = ERR_IMPORT_ERROR_3
        new_env_df = None
        return success, log, new_env_df

    return success, log, new_env_df

newenv_import(file_path)