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
        file_path - full path to an advantix csv file
    Returns:
        success - status
        log - error message
        advantix_df - pandas dataframe representing advantix data file,
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
    # # converts data and uses only columns from CONST_ADVANTIX_COL_LIST
    # success, log, advantix_df = advantix_convert(advantix_raw_df)
    # if not success:
    #     return success, log, None

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


newenv_import(file_path)