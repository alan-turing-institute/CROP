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
SQL_CONNECTION_STRING = make_conn_string(
    SQL_ENGINE,
    SQL_USER,
    parse.quote(SQL_PASSWORD),
    SQL_HOST,
    SQL_PORT,
)
SQL_DBNAME = (
    os.environ["CROP_SQL_DBNAME"].strip().lower()
    if "CROP_SQL_DBNAME" in os.environ
    else "DUMMY"
)
SQL_DEFAULT_DBNAME = "postgres"
SQL_SSLMODE = "require"

# same for the temporary db used for unit testing
SQL_TEST_USER = (
    os.environ["CROP_SQL_TESTUSER"].strip()
    if "CROP_SQL_TESTUSER" in os.environ
    else "DUMMY"
)
SQL_TEST_PASSWORD = (
    os.environ["CROP_SQL_TESTPASS"].strip()
    if "CROP_SQL_TESTPASS" in os.environ
    else "DUMMY"
)
SQL_TEST_HOST = (
    os.environ["CROP_SQL_TESTHOST"].strip()
    if "CROP_SQL_TESTHOST" in os.environ
    else "DUMMY"
)
SQL_TEST_PORT = (
    os.environ["CROP_SQL_TESTPORT"].strip()
    if "CROP_SQL_TESTPORT" in os.environ
    else "DUMMY"
)
SQL_TEST_DBNAME = (
    os.environ["CROP_SQL_TESTDBNAME"]
    if "CROP_SQL_TESTDBNAME" in os.environ
    else "test_db"
)

SQL_TEST_CONNECTION_STRING = make_conn_string(
    SQL_ENGINE,
    SQL_TEST_USER,
    parse.quote(SQL_TEST_PASSWORD),
    SQL_TEST_HOST,
    SQL_TEST_PORT,
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
MODEL_SCENARIO_TABLE_NAME = "model_scenario"
MODEL_RUN_TABLE_NAME = "model_run"
MODEL_PRODUCT_TABLE_NAME = "model_product"
MODEL_VALUE_TABLE_NAME = "model_value"
WARNING_TYPES_TABLE_NAME = "warning_types"
WARNINGS_TABLE_NAME = "warnings"

ARANET_TRH_TABLE_NAME = "aranet_trh_data"
ARANET_CO2_TABLE_NAME = "aranet_co2_data"
ARANET_AIRVELOCITY_TABLE_NAME = "aranet_airvelocity_data"
AEGIS_IRRIGATION_TABLE_NAME = "aegis_irrigation_data"

WEATHER_TABLE_NAME = "iweather"
WEATHER_FORECAST_TABLE_NAME = "weather_forecast"

# SQL Column names
ID_COL_NAME = "id"

# indexes of predictive models in the "model" table
ARIMA_MODEL_ID = 1
BSTS_MODEL_ID = 2
GES_MODEL_ID = 3
# sensor ID to use in GES model plot
GES_SENSOR_ID = 27


CONST_MAX_RECORDS = 50000

CONST_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

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
CONST_OPENWEATHERMAP_LAT = 51.45  # Clapham farm latitude
CONST_OPENWEATHERMAP_LON = 0.14  # Clapham farm longitude
CONST_OPENWEATHERMAP_UNITS = "metric"  # in API request, temperature returned in Celsius and wind speed in meter/sec

# see https://openweathermap.org/api/one-call-3
CONST_OPENWEATHERMAP_HISTORICAL_URL = (
    "https://api.openweathermap.org/data/2.5/onecall/timemachine?"
    f"lat={CONST_OPENWEATHERMAP_LAT}&lon={CONST_OPENWEATHERMAP_LON}&units={CONST_OPENWEATHERMAP_UNITS}&appid="
)  # historical weather URL without API key and requested timestamp
CONST_OPENWEATHERMAP_FORECAST_URL = (
    f"https://api.openweathermap.org/data/3.0/onecall?"
    f"lat={CONST_OPENWEATHERMAP_LAT}&lon={CONST_OPENWEATHERMAP_LON}&units={CONST_OPENWEATHERMAP_UNITS}&appid="
)  # weather forecast URL withouth API key

# Testing-related constants - filenames and filepaths

CONST_TEST_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "tests")
)
CONST_TESTDATA_BASE_FOLDER = os.path.join(CONST_TEST_DIR, "data")
CONST_TESTDATA_LOCATION_FOLDER = os.path.join(CONST_TESTDATA_BASE_FOLDER, "Locations")
CONST_TESTDATA_SENSOR_FOLDER = os.path.join(CONST_TESTDATA_BASE_FOLDER, "Sensors")
CONST_TESTDATA_WEATHER_FOLDER = os.path.join(CONST_TESTDATA_BASE_FOLDER, "Weather")
CONST_TESTDATA_ELECTRICITY_FOLDER = os.path.join(
    CONST_TESTDATA_BASE_FOLDER, "Electricity"
)
CONST_TESTDATA_ENVIRONMENT_FOLDER = os.path.join(
    CONST_TESTDATA_BASE_FOLDER, "Environmental"
)
CONST_TESTDATA_CROPGROWTH_FOLDER = os.path.join(
    CONST_TESTDATA_BASE_FOLDER, "CropGrowth"
)
CONST_TESTDATA_MODEL_FOLDER = os.path.join(CONST_TESTDATA_BASE_FOLDER, "Models")

# test data filenames
LOCATIONS_CSV = "locations.csv"  # Locations within the farm
SENSOR_CSV = "sensors.csv"  # List of sensors
SENSOR_TYPE_CSV = "sensor_types.csv"  # List of all available sensor types
LOCATION_CSV = "locations.csv"  # List of locations in the farm
SENSOR_LOCATION_CSV = "sensor_locations.csv"  # List of sensor locations
MODEL_CSV = "models.csv"  # List of models
MEASURE_CSV = "measures.csv"  # List of things to be predicted by models
# Air Velocity test data
CONST_AIR_VELOCITY_TEST_1 = "data-20200128-test1.csv"

# Crop growth synthetic data
CROP_TYPE_CSV = "crop_types.csv"
BATCH_CSV = "batches.csv"
BATCH_EVENT_CSV = "batch_events.csv"
HARVEST_CSV = "harvests.csv"

# Error messages
ERR_IMPORT_ERROR_1 = "Import file does not contain all the necessary columns."
ERR_IMPORT_ERROR_2 = "Cannot convert data into a data structure (invalid values)"
ERR_IMPORT_ERROR_3 = "Data contains empty entries"
ERR_IMPORT_ERROR_4 = "Data contains duplicates"
ERR_IMPORT_ERROR_5 = "Data contains invalid values"
