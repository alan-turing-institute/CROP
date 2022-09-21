"""
A module for constants
"""
import logging
from urllib import parse

import os
import pandas as pd

logging.basicConfig(level=logging.DEBUG)


def make_conn_string(sql_engine, sql_user, sql_password, sql_host, sql_port):
    """
    Constructs a connection string.
    Arguments:
        sql_engine
        sql_user
        sql_password
        sql_host
        sql_port

    Returns:
        connection string
    """

    return "%s://%s:%s@%s:%s" % (
        sql_engine,
        sql_user,
        parse.quote(sql_password),
        sql_host,
        sql_port,
    )


# Sensor Type Names
CONST_ADVANTICSYS = "Advanticsys"
CONST_AIR_VELOCITY = "Air_Velocity"
CONST_STARK = "Stark"
CONST_ARANET_CO2_SENSOR_TYPE = "Aranet CO2"
CONST_ARANET_AIRVELOCITY_SENSOR_TYPE = "Aranet Air Velocity"
CONST_WEATHER_SENSOR_TYPE = "Weather"
CONST_ARANET_TRH_SENSOR_TYPE = "Aranet T&RH"
CONST_AEGIS_IRRIGATION_SENSOR_TYPE = "Aegis II"

CONST_API_WEATHER_TYPE = "openweathermap"

# FILE STRUCTURE
CONST_DATA_FOLDER = "data"
CONST_TEST_FOLDER = "tests"
CONST_CORE_DATA_FOLDER = "Core"
CONST_ADVANTICSYS_FOLDER = "Advanticsys"
CONST_AIR_VELOCITY_FOLDER = "Air_Velocity"
CONST_ENV_FOLDER = "Environmental"

CONST_SENSOR_LOCATION_TESTS = "sensor_location_tests"

CONST_TEST_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", CONST_TEST_FOLDER)
)
CONST_TEST_DIR_DATA = os.path.join(CONST_TEST_DIR, CONST_DATA_FOLDER)
CONST_COREDATA_DIR = os.path.join(
    CONST_TEST_DIR, CONST_DATA_FOLDER, CONST_CORE_DATA_FOLDER
)
CONST_ADVANTICSYS_DIR = os.path.join(
    CONST_TEST_DIR, CONST_DATA_FOLDER, CONST_ADVANTICSYS_FOLDER
)
CONST_ENV_DIR = os.path.join(CONST_TEST_DIR, CONST_DATA_FOLDER, CONST_ENV_FOLDER)

# Core data
SENSOR_CSV = "Sensors.csv"  # List of sensors
SENSOR_TYPE_CSV = "Sensortypes.csv"  # list of all available sensor types
LOCATION_CSV = "locations.csv"  # List of locations in the farm

# ADVANTICSYS IMPORT
CONST_ADVANTICSYS_COL_TIMESTAMP = "Timestamp"
CONST_ADVANTICSYS_COL_MODBUSID = "Modbus ID"
CONST_ADVANTICSYS_COL_TEMPERATURE = "Temperature"
CONST_ADVANTICSYS_COL_HUMIDITY = "Humidity"
CONST_ADVANTICSYS_COL_CO2LEVEL = "CO2 Level"
CONST_ADVANTICSYS_COL_LIST = [
    CONST_ADVANTICSYS_COL_TIMESTAMP,
    CONST_ADVANTICSYS_COL_MODBUSID,
    CONST_ADVANTICSYS_COL_TEMPERATURE,
    CONST_ADVANTICSYS_COL_HUMIDITY,
    CONST_ADVANTICSYS_COL_CO2LEVEL,
]

CONST_ADVANTICSYS_TIMESTAMP_MIN = pd.to_datetime("2016-01-01")
CONST_ADVANTICSYS_TIMESTAMP_MAX = pd.to_datetime("2031-12-31")
CONST_ADVANTICSYS_MODBUSID_MIN = 1
CONST_ADVANTICSYS_MODBUSID_MAX = 1000
CONST_ADVANTICSYS_TEMPERATURE_MIN = -273
CONST_ADVANTICSYS_TEMPERATURE_MAX = 100
CONST_ADVANTICSYS_HUMIDITY_MIN = 0
CONST_ADVANTICSYS_HUMIDITY_MAX = 100
CONST_ADVANTICSYS_CO2LEVEL_MIN = 0
CONST_ADVANTICSYS_CO2LEVEL_MAX = 1000

# Advanticsys test data
CONST_ADVANTICSYS_TEST_1 = "data-20190821-test1.csv"  # Healthy data file
CONST_ADVANTICSYS_TEST_2 = (
    "data-20190821-test2.csv"  # Few rows, one column is misspelled
)
CONST_ADVANTICSYS_TEST_3 = "data-20190821-test3.csv"  # Few rows, timestamp is wrong
CONST_ADVANTICSYS_TEST_4 = "data-20190821-test4.csv"  # Few rows, mobdusid is wrong
# Few rows, temeprature is wrong
CONST_ADVANTICSYS_TEST_5 = "data-20190821-test5.csv"
CONST_ADVANTICSYS_TEST_6 = "data-20190821-test6.csv"  # Few rows, humidity is wrong
CONST_ADVANTICSYS_TEST_7 = "data-20190821-test7.csv"  # Few rows, co2 level is wrong
# Temperature and humidity empty
CONST_ADVANTICSYS_TEST_8 = "data-20190821-test8.csv"
CONST_ADVANTICSYS_TEST_9 = "data-20190821-test9.csv"  # Duplicate values
CONST_ADVANTICSYS_TEST_10 = "data-20190821-test10.csv"  # Wrong sensor id

# Air Velocity test data
CONST_AIR_VELOCITY_TEST_1 = "data-20200128-test1.csv"

# New environmental sensors IMPORT
CONST_NEW_ENV_COL_TIMESTAMP = "Logger timestamp"
CONST_NEW_ENV_COL_DEVICE = "Device Address"
CONST_NEW_ENV_COL_UPTIME = "Uptime"
CONST_NEW_ENV_COL_BATTERY = "Battery"
CONST_NEW_ENV_COL_VALIDITY = "Validity"
CONST_NEW_ENV_COL_CH0 = "Ch.0"
CONST_NEW_ENV_COL_CH1 = "Ch.1"
CONST_NEW_ENV_COL_CH2 = "Ch.2"
CONST_NEW_ENV_COL_CH3 = "Ch.3"
CONST_NEW_ENV_COL_OPT3001 = "OPT3001"
CONST_NEW_ENV_COL_CO2 = "Cozir CO2"
CONST_NEW_ENV_COL_TEMPERATURE = "SHT21 Temp"
CONST_NEW_ENV_COL_HUMIDITY = "SHT21 Humid"
CONST_NEW_ENV_COL_DS_TEMP = "DS3231 Temp"
CONST_NEW_ENV_COL_LIST = [
    CONST_NEW_ENV_COL_TIMESTAMP,
    CONST_NEW_ENV_COL_DEVICE,
    CONST_NEW_ENV_COL_UPTIME,
    CONST_NEW_ENV_COL_UPTIME,
    CONST_NEW_ENV_COL_BATTERY,
    CONST_NEW_ENV_COL_VALIDITY,
    CONST_NEW_ENV_COL_CH0,
    CONST_NEW_ENV_COL_CH1,
    CONST_NEW_ENV_COL_CH2,
    CONST_NEW_ENV_COL_CH3,
    CONST_NEW_ENV_COL_OPT3001,
    CONST_NEW_ENV_COL_CO2,
    CONST_NEW_ENV_COL_TEMPERATURE,
    CONST_NEW_ENV_COL_HUMIDITY,
    CONST_NEW_ENV_COL_DS_TEMP,
]

# New Environmental sensors test data
CONST_NEW_ENV_TEST_1 = "raw-20200124-test1.csv"  # Healthy data file

# Error messages
ERR_IMPORT_ERROR_1 = "Import file does not contain all the necessary columns."
ERR_IMPORT_ERROR_2 = "Cannot convert data into a data structure (invalid values)"
ERR_IMPORT_ERROR_3 = "Data contains empty entries"
ERR_IMPORT_ERROR_4 = "Data contains duplicates"
ERR_IMPORT_ERROR_5 = "Data contains invalid values"

# STARK
STARK_USERNAME = (
    os.environ["CROP_STARK_USERNAME"].strip()
    if "CROP_STARK_USERNAME" in os.environ
    else "DUMMY"
)
STARK_PASS = (
    os.environ["CROP_STARK_PASS"].strip()
    if "CROP_STARK_PASS" in os.environ
    else "DUMMY"
)

# Hyper.ag
CONST_CROP_HYPER_APIKEY = (
    os.environ["CROP_HYPER_APIKEY"].strip()
    if "CROP_HYPER_APIKEY" in os.environ
    else "DUMMY"
)

# openweatherdata API
CONST_OPENWEATHERMAP_APIKEY = (
    os.environ["CROP_OPENWEATHERMAP_APIKEY"].strip()
    if "CROP_OPENWEATHERMAP_APIKEY" in os.environ
    else "DUMMY"
)

# Create connection string
SQL_ENGINE = "postgresql"
SQL_USER = (
    os.environ["CROP_SQL_USER"].strip() if "CROP_SQL_USER" in os.environ else "DUMMY"
)
SQL_PASSWORD = (
    os.environ["CROP_SQL_PASS"].strip() if "CROP_SQL_PASS" in os.environ else "DUMMY"
)
SQL_HOST = (
    os.environ["CROP_SQL_HOST"].strip() if "CROP_SQL_HOST" in os.environ else "DUMMY"
)
SQL_PORT = (
    os.environ["CROP_SQL_PORT"].strip() if "CROP_SQL_PORT" in os.environ else "DUMMY"
)
SQL_DBNAME = (
    os.environ["CROP_SQL_DBNAME"].strip().lower()
    if "CROP_SQL_DBNAME" in os.environ
    else "DUMMY"
)
SQL_DEFAULT_DBNAME = "postgres"
SQL_SSLMODE = "require"

SQL_TEST_DBNAME = "test_db"

SQL_CONNECTION_STRING = make_conn_string(
    SQL_ENGINE,
    SQL_USER,
    parse.quote(SQL_PASSWORD),
    SQL_HOST,
    SQL_PORT,
)

SQL_CONNECTION_STRING_DEFAULT = "%s/%s" % (SQL_CONNECTION_STRING, SQL_DEFAULT_DBNAME)
SQL_CONNECTION_STRING_CROP = "%s/%s" % (SQL_CONNECTION_STRING, SQL_DBNAME)

# SQL Table names
SENSOR_TABLE_NAME = "sensors"
SENSOR_TYPE_TABLE_NAME = "sensor_types"
LOCATION_TABLE_NAME = "locations"
ADVANTICSYS_READINGS_TABLE_NAME = "advanticsys_data"
TINYTAG_READINGS_TABLE_NAME = "tinytag_data"
ENERGY_READINGS_TABLE_NAME = "utc_energy_data"
SENSOR_LOCATION_TABLE_NAME = "sensor_location"
SENSOR_UPLOAD_LOG_TABLE_NAME = "sensor_upload_log"
MODEL_TABLE_NAME = "model"
MODEL_MEASURE_TABLE_NAME = "model_measure"
MODEL_RUN_TABLE_NAME = "model_run"
MODEL_PRODUCT_TABLE_NAME = "model_product"
MODEL_VALUE_TABLE_NAME = "model_value"
TEST_MODEL_TABLE_NAME = "test_model"
TEST_MODEL_MEASURE_TABLE_NAME = "test_model_measure"
TEST_MODEL_RUN_TABLE_NAME = "test_model_run"
TEST_MODEL_PRODUCT_TABLE_NAME = "test_model_product"
TEST_MODEL_VALUE_TABLE_NAME = "test_model_value"

ARANET_TRH_TABLE_NAME = "aranet_trh_data"
ARANET_CO2_TABLE_NAME = "aranet_co2_data"
ARANET_AIRVELOCITY_TABLE_NAME = "aranet_airvelocity_data"
AEGIS_IRRIGATION_TABLE_NAME = "aegis_irrigation_data"

WEATHER_TABLE_NAME = "iweather"
WEATHER_FORECAST_TABLE_NAME = "weather_forecast"

# SQL Column names
ID_COL_NAME = "id"

CONST_MAX_RECORDS = 50000

CONST_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# Warnings log

WARNING_PROP_LOW_TEMPR = "Temperature is low in propagation, add heater"
WARNING_NO_DATA_PROP = "Missing data in propagation - check sensor battery"

#
CROP_TYPE_TABLE_NAME = "crop_types"
BATCH_TABLE_NAME = "batches"
BATCH_EVENT_TABLE_NAME = "batch_events"
HARVEST_TABLE_NAME = "harvests"

GROWAPP_IP = os.environ["GROWAPP_IP"] if "GROWAPP_IP" in os.environ else "DUMMY"
GROWAPP_DB = (
    os.environ["GROWAPP_DATABASE"] if "GROWAPP_DATABASE" in os.environ else "DUMMY"
)
GROWAPP_USER = (
    os.environ["GROWAPP_USERNAME"] if "GROWAPP_USERNAME" in os.environ else "DUMMY"
)
GROWAPP_PASSWORD = (
    os.environ["GROWAPP_PASS"] if "GROWAPP_PASS" in os.environ else "DUMMY"
)
GROWAPP_SCHEMA = (
    os.environ["GROWAPP_SCHEMA"] if "GROWAPP_SCHEMA" in os.environ else "DUMMY"
)

# OPENWEATHERMAP API misc constants
CONST_OPENWEATHERMAP_LAT = 51.45 # Clapham farm latitude
CONST_OPENWEATHERMAP_LON = 0.14 # Clapham farm longitude
CONST_OPENWEATHERMAP_UNITS = "metric" # in API request, temperature returned in Celsius and wind speed in meter/sec

# see https://openweathermap.org/api/one-call-3
CONST_OPENWEATHERMAP_HISTORICAL_URL = "https://api.openweathermap.org/data/3.0/onecall/timemachine?"\
f"lat={CONST_OPENWEATHERMAP_LAT}&lon={CONST_OPENWEATHERMAP_LON}&units={CONST_OPENWEATHERMAP_UNITS}&appid=" # historical weather URL without API key and requested timestamp
CONST_OPENWEATHERMAP_FORECAST_URL = f"https://api.openweathermap.org/data/3.0/onecall?"\
f"lat={CONST_OPENWEATHERMAP_LAT}&lon={CONST_OPENWEATHERMAP_LON}&units={CONST_OPENWEATHERMAP_UNITS}&appid=" # weather forecast URL withouth API key
