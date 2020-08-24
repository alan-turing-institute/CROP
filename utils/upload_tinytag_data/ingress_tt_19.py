import pandas as pd
import os
import csv


from constants import (
    CONST_TINYTAG_DIR,
    CONST_TINYTAG_TEST_2019,
    ERR_IMPORT_ERROR_1,
    ERR_IMPORT_ERROR_2,
    ERR_IMPORT_ERROR_3,
    CONST_TINYTAG,
    CONST_TINYTAG_COL_LIST,
    CONST_TINYTAG_COL_TEMPERATURE,
    CONST_TINYTAG_COL_TIMESTAMP,
    CONST_TINYTAG_COL_NAME,
    CONST_TINYTAG_COL_SENSOR_NAME,
)

from structure import SensorClass, TypeClass, ReadingsTinyTagClass


file_path = os.path.join(CONST_TINYTAG_DIR, CONST_TINYTAG_TEST_2019)


def tinytag_import(file_path):
    """
    Reads in tinytag csv file as pandas data frame and performs checks

    Args:
        file_path - full path to an advanticsys csv file
    Returns:
        success - status
        log - error message
        tinytag_df - pandas dataframe representing advanticsys data file,
        returns None if data is invalid
    """

    tinytag_raw_df = tinytag_read_csv(file_path)
    # print(tinytag_raw_df)

    return tinytag_df_checks(tinytag_raw_df)


def tinytag_df_checks(tinytag_raw_df):
    """
    Args
    Return
    """
    # Checks if df exists
    if not isinstance(tinytag_raw_df, pd.DataFrame):
        return False, "Not a pandas dataframe", None

    # Checks if df is empty
    if tinytag_raw_df.empty:
        return False, "Dataframe empty", None

    # converts data and uses only columns from CONST_TINYTAG_COL_LIST
    success, log, tinytag_df = tinytag_convert(tinytag_raw_df)
    if not success:
        return success, log, None


def tinytag_read_csv(file_path):
    """
    Reads in advanticsys csv file as pandas data frame.

    Args:
        file_path - full path to an advanticsys csv file
    Returns:
        df - pandas dataframe representing advanticsys data file
    """
    df = pd.read_csv(file_path)

    return df


def tinytag_convert(tinytag_raw_df):
    """
    Prepares Tinytag dataframe to be imported to database by selecting only neccessary columns
        and converting to correct data types.

    Args:
        advanticsys_raw_df - pandas dataframe representing advanticsys data file
    Returns:
        success - status
        log - error message
        tinytag_df - converted pandas dataframe
    """

    success = True
    log = None

    try:
        # read the two existing columns iwth temperature and timestamp
        tinytag_df = tinytag_raw_df[
            [CONST_TINYTAG_COL_TEMPERATURE, CONST_TINYTAG_COL_TIMESTAMP, "loc"]
        ].copy()

        # inserts a new column with the name "sensor_name"
        # and fills it with the value of the name of the sensor.
        tinytag_df.rename(
            columns={
                CONST_TINYTAG_COL_TEMPERATURE: "temperature",
                CONST_TINYTAG_COL_TIMESTAMP: "timestamp",
                "loc": "sensor_name",
            },
            inplace=True,
        )

    except:
        success = False
        log = "cannnot convert columns in tinytag history"
        return success, log, tinytag_df

    # convert to expected types
    try:
        tinytag_df["timestamp"] = pd.to_datetime(
            tinytag_df["timestamp"], format="%d/%m/%Y %H:%M",
        )
        tinytag_df["temperature"] = tinytag_df["temperature"].astype("float64")

    except:
        success = False
        log = ERR_IMPORT_ERROR_2
        tinytag_df = None
        return success, log, tinytag_df

    try:
        tinytag_df = tinytag_df.fillna(0)
    except:
        # print(tinytag_df[tinytag_df.isna().any(axis=1)])
        success = False
        log = "Cannot replace NA with 0"
        return success, log, tinytag_df

    # check for missing values
    if tinytag_df.isnull().values.any():
        success = False
        log = ERR_IMPORT_ERROR_3
        tinytag_df = None
        return success, log, tinytag_df

    return success, log, tinytag_df


def insert_tinytag_data(session, tinytag_df):
    """
    The function will take the prepared tinytag data frame from the ingress module
    and find sensor id with respect to modbusid and sensor type and insert data into the db.
    -session: an open sqlalchemy session
    -tinytag_df: dataframe containing a checked tinytag df
    -cnt_dupl: counts duplicate values
    """

    result = True
    log = ""
    cnt_dupl = 0
    cnt_new = 0

    # Gets the the assigned int id of the "TinyTag" type
    try:
        tt_type_id = (
            session.query(TypeClass)
            .filter(TypeClass.sensor_type == CONST_TINYTAG)
            .first()
            .id
        )
    except:
        result = False
        log = "Sensor type {} was not found.".format(CONST_TINYTAG)
        return result, log

    # Gets the sensor_id of the sensor with type=tinytag and device_id=sensor_name
    for _, row in tinytag_df.iterrows():

        tt_device_id = row[CONST_TINYTAG_COL_NAME]
        tt_timestamp = row[CONST_TINYTAG_COL_TIMESTAMP]

        try:
            tt_sensor_id = (
                session.query(SensorClass)
                .filter(SensorClass.device_id == str(tt_device_id))
                .filter(SensorClass.type_id == tt_type_id)
                .first()
                .id
            )
        except:
            tt_sensor_id = -1
            result = False
            log = "{} sensor with {} = {} was not found.".format(
                CONST_TINYTAG, CONST_TINYTAG_COL_NAME, str(tt_device_id)
            )
            break

        # check if data entry already exists
        if tt_sensor_id != -1:

            found = False

            query_result = (
                session.query(ReadingsTinyTagClass)
                .filter(ReadingsTinyTagClass.sensor_id == tt_sensor_id)
                .filter(ReadingsTinyTagClass.timestamp == tt_timestamp)
                .first()
            )

            if query_result is not None:
                found = True

            try:
                if not found:
                    data = ReadingsTinyTagClass(
                        sensor_id=tt_sensor_id,
                        timestamp=tt_timestamp,
                        temperature=row[CONST_TINYTAG_COL_TEMPERATURE],
                        sensor_name=row[CONST_TINYTAG_COL_NAME],
                    )
                    session.add(data)

                    cnt_new += 1
                else:
                    cnt_dupl += 1
            except:
                result = False
                log = "Cannot insert new data to database"

    if result:
        log = "New: {} (uploaded); Duplicates: {} (ignored)".format(cnt_new, cnt_dupl)

    return result, log


tinytag_import(file_path)

