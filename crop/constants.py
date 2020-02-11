"""
A module for constants
"""
import os
import pandas as pd

# FILE STRUCTURE
CONST_DATA_FOLDER = "data"
CONST_TEST_FOLDER = "tests"
CONST_ADVANTIX_FOLDER = "Advantix"

CONST_TEST_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    CONST_TEST_FOLDER))

CONST_TEST_DIR_DATA = os.path.join(CONST_TEST_DIR, CONST_DATA_FOLDER)

# ADVANTIX IMPORT
CONST_ADVANTIX_COL_TIMESTAMP = "Timestamp"
CONST_ADVANTIX_COL_MODBUSID = "Modbus ID"
CONST_ADVANTIX_COL_TEMPERATURE = "Temperature"
CONST_ADVANTIX_COL_HUMIDITY = "Humidity"
CONST_ADVANTIX_COL_CO2LEVEL = "CO2 Level"
CONST_ADVANTIX_COL_LIST = [
    CONST_ADVANTIX_COL_TIMESTAMP,
    CONST_ADVANTIX_COL_MODBUSID,
    CONST_ADVANTIX_COL_TEMPERATURE,
    CONST_ADVANTIX_COL_HUMIDITY,
    CONST_ADVANTIX_COL_CO2LEVEL,
]

CONST_ADVANTIX_TIMESTAMP_MIN = pd.to_datetime("2016-01-01")
CONST_ADVANTIX_TIMESTAMP_MAX = pd.to_datetime("2031-12-31")
CONST_ADVANTIX_MODBUSID_MIN = 1
CONST_ADVANTIX_MODBUSID_MAX = 1000
CONST_ADVANTIX_TEMPERATURE_MIN = -273
CONST_ADVANTIX_TEMPERATURE_MAX = 100
CONST_ADVANTIX_HUMIDITY_MIN = 0
CONST_ADVANTIX_HUMIDITY_MAX = 100
CONST_ADVANTIX_CO2LEVEL_MIN = 0
CONST_ADVANTIX_CO2LEVEL_MAX = 1000

# Advantix test data
CONST_ADVANTIX_TEST_1 = "data-20190821-test1.csv" # Healthy data file
CONST_ADVANTIX_TEST_2 = "data-20190821-test2.csv" # Few rows, one column is misspelled
CONST_ADVANTIX_TEST_3 = "data-20190821-test3.csv" # Few rows, timestamp is wrong
CONST_ADVANTIX_TEST_4 = "data-20190821-test4.csv" # Few rows, mobdusid is wrong
CONST_ADVANTIX_TEST_5 = "data-20190821-test5.csv" # Few rows, temeprature is wrong
CONST_ADVANTIX_TEST_6 = "data-20190821-test6.csv" # Few rows, humidity is wrong
CONST_ADVANTIX_TEST_7 = "data-20190821-test7.csv" # Few rows, co2 level is wrong
CONST_ADVANTIX_TEST_8 = "data-20190821-test8.csv" # Temperature and humidity empty
CONST_ADVANTIX_TEST_9 = "data-20190821-test9.csv" # Duplicate values

# Error messages
ERR_IMPORT_ERROR_1 = "Import file does not contain all the necessary columns."
ERR_IMPORT_ERROR_2 = "Cannot convert data into a data structure (invalid values)"
ERR_IMPORT_ERROR_3 = "Data contains empty entries"
ERR_IMPORT_ERROR_4 = "Data contains duplicates"
ERR_IMPORT_ERROR_5 = "Data contains invalid values"


# Create connection string
SQL_ENGINE = "postgresql"
SQL_DBNAME = "crop_db"
SQL_DEFAULT_DBNAME = 'postgres'
SQL_USER = os.environ['AZURE_SQL_USER']
SQL_PASSWORD = os.environ['AZURE_SQL_PASS']
SQL_HOST = os.environ['AZURE_SQL_HOST']
SQL_PORT = os.environ['AZURE_SQL_PORT']
SQL_SSLMODE = "require"

SQL_CONNECTION_STRING = "%s://%s:%s@%s:%s" % (SQL_ENGINE, SQL_USER, SQL_PASSWORD,
                                              SQL_HOST, SQL_PORT)

SQL_CONNECTION_STRING_DEFAULT = "%s/%s" % (SQL_CONNECTION_STRING, SQL_DEFAULT_DBNAME)
SQL_CONNECTION_STRING_CROP = "%s/%s" % (SQL_CONNECTION_STRING, SQL_DBNAME)

PSYCOPG2_SQL_CONNECTION_STRING_DEFAULT = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(SQL_HOST, SQL_USER, SQL_DEFAULT_DBNAME, SQL_PASSWORD, SQL_SSLMODE)

# SQL Table names
SENSOR_TABLE_NAME = 'sensor'
SENSOR_TYPE_TABLE_NAME = 'sensor_type'
LOCATION_TABLE_NAME = 'location'
ADVANTIX_READINGS_TABLE_NAME = 'advantix'

