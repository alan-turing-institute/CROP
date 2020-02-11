"""
Python module to perform data ingress operations

"""

import pandas as pd
import os
from crop.create_db import create_database
from crop.constants import (
    CONST_ADVANTIX_COL_LIST,
    CONST_ADVANTIX_COL_TIMESTAMP,
    CONST_ADVANTIX_COL_MODBUSID,
    CONST_ADVANTIX_COL_TEMPERATURE,
    CONST_ADVANTIX_COL_HUMIDITY,
    CONST_ADVANTIX_COL_CO2LEVEL,
    ERR_IMPORT_ERROR_1,
    ERR_IMPORT_ERROR_2,
    ERR_IMPORT_ERROR_3,
    ERR_IMPORT_ERROR_4,
    ERR_IMPORT_ERROR_5,
    CONST_ADVANTIX_TIMESTAMP_MIN,
    CONST_ADVANTIX_TIMESTAMP_MAX,
    CONST_ADVANTIX_MODBUSID_MIN,
    CONST_ADVANTIX_MODBUSID_MAX,
    CONST_ADVANTIX_TEMPERATURE_MIN,
    CONST_ADVANTIX_TEMPERATURE_MAX,
    CONST_ADVANTIX_HUMIDITY_MIN,
    CONST_ADVANTIX_HUMIDITY_MAX,
    CONST_ADVANTIX_CO2LEVEL_MIN,
    CONST_ADVANTIX_CO2LEVEL_MAX,
    CONST_TEST_DIR_DATA,
    CONST_ADVANTIX_FOLDER,
    CONST_ADVANTIX_TEST_1,
    SQL_CONNECTION_STRING, 
    SQL_DBNAME
)

file_path = os.path.join(CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_1)

def advantix_import(file_path):
    """
    Reads in advantix csv file as pandas data frame and performs checks

    Args:
        file_path - full path to an advantix csv file
    Returns:
        success - status
        log - error message
        advantix_df - pandas dataframe representing advantix data file, returns None if data is invalid
    """
  
    advantix_raw_df = advantix_read_csv(file_path)

    return advantix_df_checks(advantix_raw_df)

def advantix_df_checks(advantix_raw_df):
    """
    Args
    Return
    """
    # Checks if df exists
    if not isinstance(advantix_raw_df, pd.DataFrame):
        return False, "Not a pandas dataframe", None
    
    # Checks if df is empty
    if advantix_raw_df.empty:
        return False, "Dataframe empty", None

    # Checks structure
    success, log = advantix_check_structure(advantix_raw_df)
    if not success: return success, log, None
   
    # converts data and uses only columns from CONST_ADVANTIX_COL_LIST
    success, log, advantix_df = advantix_convert(advantix_raw_df)
    if not success: return success, log, None

    # Checks for validity
    success, log = advantix_df_validity(advantix_df)
    if not success: return success, log, None

    return success, log, advantix_df

def advantix_read_csv(file_path):
    """
    Reads in advantix csv file as pandas data frame.

    Args:
        file_path - full path to an advantix csv file
    Returns:
        df - pandas dataframe representing advantix data file
    """

    df = pd.read_csv(file_path)

    return df

def advantix_check_structure(advantix_df):
    """
    Checks if advantix dataframe has expected structure

    Args:
        advantix_df - pandas dataframe representing advantix data file
    Returns:
        True/False depending on whether the dataframe has the correct structure
        Error message
    """
    
    # Check if all the nessecary columns are present in the dataframe
    for advantix_column in CONST_ADVANTIX_COL_LIST:
        if not advantix_column in advantix_df.columns:
            return False, ERR_IMPORT_ERROR_1
    
    return True, None

def advantix_convert(advantix_raw_df):
    """
    Prepares Adavantix dataframe to be imported to database by selecting only neccessary columns 
        and converting to correct data types.
    
    Args:
        advantix_raw_df - pandas dataframe representing advantix data file
    Returns:
        success - status
        log - error message
        advantix_df - converted pandas dataframe
    """
    
    success = True
    log = None

    try:
        advantix_df = advantix_raw_df[CONST_ADVANTIX_COL_LIST]
    except:
        success = False
        log = ERR_IMPORT_ERROR_1 + ": " + ','.join(CONST_ADVANTIX_COL_LIST)
        advantix_df = None
        return success, log, advantix_df

    # convert to expected types
    try:
        advantix_df[CONST_ADVANTIX_COL_TIMESTAMP] = pd.to_datetime(advantix_df[CONST_ADVANTIX_COL_TIMESTAMP], format="%Y-%m-%dT%H:%M:%S.%f") # 
        advantix_df[CONST_ADVANTIX_COL_MODBUSID] = advantix_df[CONST_ADVANTIX_COL_MODBUSID].astype('int16')
        advantix_df[CONST_ADVANTIX_COL_TEMPERATURE] = advantix_df[CONST_ADVANTIX_COL_TEMPERATURE].astype('float64')
        advantix_df[CONST_ADVANTIX_COL_HUMIDITY] = advantix_df[CONST_ADVANTIX_COL_HUMIDITY].astype('float64')
        advantix_df[CONST_ADVANTIX_COL_CO2LEVEL] = advantix_df[CONST_ADVANTIX_COL_CO2LEVEL].astype('float64')
    except:
        success = False
        log = ERR_IMPORT_ERROR_2
        advantix_df = None
        return success, log, advantix_df

    # check for missing values
    if (advantix_df.isnull().values.any()):
        success = False
        log = ERR_IMPORT_ERROR_3
        advantix_df = None
        return success, log, advantix_df

    return success, log, advantix_df

def advantix_df_validity(advantix_df):
    """
    Checks if advantix dataframe has expected structure

    Args:
        advantix_df - pandas dataframe representing advantix data file
    Returns:
        True/False depending on whether the dataframe has the correct stricture
        Error message
    """

    success = True
    log = ""

    # Checking for duplicates
    duplicates = advantix_df[advantix_df.duplicated()]
    if (len(duplicates) > 0):
        success = False
        log = ERR_IMPORT_ERROR_4 + ". Check the following entries: " + str(list(duplicates.index))
    if not success: return success, log

    col_names = [CONST_ADVANTIX_COL_TIMESTAMP, CONST_ADVANTIX_COL_MODBUSID, CONST_ADVANTIX_COL_TEMPERATURE, 
        CONST_ADVANTIX_COL_HUMIDITY, CONST_ADVANTIX_COL_CO2LEVEL]
    col_mins = [CONST_ADVANTIX_TIMESTAMP_MIN, CONST_ADVANTIX_MODBUSID_MIN, CONST_ADVANTIX_TEMPERATURE_MIN,
        CONST_ADVANTIX_HUMIDITY_MIN, CONST_ADVANTIX_CO2LEVEL_MIN]
    col_maxs = [CONST_ADVANTIX_TIMESTAMP_MAX, CONST_ADVANTIX_MODBUSID_MAX, CONST_ADVANTIX_TEMPERATURE_MAX,
        CONST_ADVANTIX_HUMIDITY_MAX, CONST_ADVANTIX_CO2LEVEL_MAX]
   
    # Check every column
    for col_name, col_min, col_max in zip(col_names, col_mins, col_maxs):
        success, log = advantix_df_check_range(advantix_df, col_name, col_min, col_max)
        if not success: return success, log

    return success, log

def advantix_df_check_range(advantix_df, col_name, col_min, col_max):
    """
    Checks if value in a dataframe for a specific column are within a range. If not creates an error message.

    Args: 
        advantix_df - pandas dataframe representing advantix data file
        col_name - column name
        col_min - minimum value
        col_max - maximum value
    Returns:
        success - status
        log - error message
    """

    success = True
    log = ""

    out_of_range_df = advantix_df[
        (advantix_df[col_name] < col_min) | 
        (advantix_df[col_name] > col_max)]
    
    if len(out_of_range_df) > 0:
        success = False
        log = ERR_IMPORT_ERROR_5 + " <" + col_name + \
            "> out of range (min = %f, max = %f)" % (col_min, col_max) + \
            " Entries: " + str(list(out_of_range_df.index))

    return success, log


#dont rename create a new one. 
# def advantix_df_rename_headers(advantix_df):

#     success = True
#     log = ""

#     advantix_df_copy= advantix_df.copy()
#     advantix_df_copy.rename(columns = {CONST_ADVANTIX_COL_MODBUSID:'Modbusid',
#                                   CONST_ADVANTIX_COL_CO2LEVEL: 'Co2'}, inplace=True)

#     return success, log, advantix_df_copy

def advantix_prep_for_import(advantix_df):
    """
    The function will take the raw advantix data frame and find sensor id with respect 
    to modbusid and sensor type and 

    """

    result = None

    # find unique modbus ids

    unq_modbus_ids = advantix_df[CONST_ADVANTIX_COL_MODBUSID].unique()


    # match modbus ids and sernsor type with sensor ids
    # create new df

    return result
