import pandas as pd
import os
import csv


from __app__.crop.constants import (
    ERR_IMPORT_ERROR_1,
    ERR_IMPORT_ERROR_2,
    ERR_IMPORT_ERROR_3,
    CONST_TINYTAG,
    CONST_TINYTAG_COL_LIST,
    CONST_TINYTAG_COL_TEMPERATURE,
    CONST_TINYTAG_COL_TIMESTAMP,
    CONST_TINYTAG_COL_NAME,
    SQL_CONNECTION_STRING,
)

from __app__.crop.structure import SensorClass, TypeClass, ReadingsTinyTagClass

from __app__.crop.db import connect_db, session_open, session_close


file_path = "C:\\Users\\Flora\\OneDrive - The Alan Turing Institute\\Turing\\2.UrbanAgriculture\\Data_original\\TinyTags\\processed_data\\TinyTag\\tinytag_all.csv"


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
    success = True
    log = None

    # Checks if df exists
    if not isinstance(tinytag_raw_df, pd.DataFrame):
        return False, "Not a pandas dataframe", None

    # Checks if df is empty
    if tinytag_raw_df.empty:
        return False, "Dataframe empty", None

    # converts data and uses only columns from CONST_TINYTAG_COL_LIST
    success, log, tinytag_df = tinytag_convert(
        tinytag_raw_df, tinytag_raw_df.columns[4]
    )

    if not success:
        return success, log, None

    return success, log, tinytag_df


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


def tinytag_convert(tinytag_raw_df, sensor_name):
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
        # read the two existing columns with temperature and timestamp
        tinytag_df = tinytag_raw_df[[sensor_name, "DateTime"]].copy()

        # inserts a new column with the name "sensor_name"
        # and fills it with the value of the name of the sensor.
        tinytag_df.insert(0, CONST_TINYTAG_COL_NAME, sensor_name, True)
        tinytag_df.rename(
            columns={
                sensor_name: "temperature",
                "DateTime": CONST_TINYTAG_COL_TIMESTAMP,
            },
            inplace=True,
        )

    except:
        success = False
        log = "cannnot convert columns in tinytag history"
        return success, log, tinytag_df

    # print(tinytag_df.head())
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

    print(tinytag_df)
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
        print(log)
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
            print(log)
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
                        # sensor_name=row[CONST_TINYTAG_COL_NAME],
                    )
                    session.add(data)

                    cnt_new += 1
                else:
                    cnt_dupl += 1
            except:
                result = False
                log = "Cannot insert new data to database"
                print(log)

    if result:
        log = "New: {} (uploaded); Duplicates: {} (ignored)".format(cnt_new, cnt_dupl)
        print(log)

    print(result)
    return result, log


def main():
    print("starting importing tinytag 18")
    local_connection_string = "%s://%s:%s@%s:%s" % (
        "postgresql",
        "postgres",
        "crop",
        "localhost",
        "5433",
    )

    testdb_connection_string = SQL_CONNECTION_STRING

    success, log, engine = connect_db(testdb_connection_string, "app_db")

    result, log, df = tinytag_import(file_path)

    tinytag_session = session_open(engine)

    print("putting data")

    insert_tinytag_data(tinytag_session, df)

    print("putting data2")

    session_close(tinytag_session)
    print("finished session")


if __name__ == "__main__":
    main()
