"""
Python module to import data using the Hyper.ag API
"""

from collections.abc import Iterable
import logging
import time
from datetime import datetime, timedelta
import requests
import pandas as pd

from sqlalchemy import and_
from sqlalchemy.exc import ProgrammingError

from .db import connect_db, session_open, session_close
from .structure import (
    TypeClass,
    SensorClass,
    ReadingsAranetTRHClass,
    ReadingsAranetCO2Class,
    ReadingsAranetAirVelocityClass,
    ReadingsAegisIrrigationClass,
)
from .constants import (
    CONST_CROP_HYPER_APIKEY,
    CONST_ARANET_TRH_SENSOR_TYPE,
    CONST_ARANET_CO2_SENSOR_TYPE,
    CONST_ARANET_AIRVELOCITY_SENSOR_TYPE,
    CONST_AEGIS_IRRIGATION_SENSOR_TYPE,
)

from .utils import log_upload_event
from .sensors import get_sensor_readings_db_timestamps


CONST_CHECK_URL_PATH = (
    "https://zcf.hyper.systems/api/sites/1/analytics/v3/device_metrics"
)

READINGS_DICTS = [
    {
        "readings_class": ReadingsAranetTRHClass,
        "sensor_type": CONST_ARANET_TRH_SENSOR_TYPE,
        "columns": [
            {
                "api_name": "aranet_ambient_temperature",
                "df_name": "Temperature",
                "db_name": "temperature",
            },
            {
                "api_name": "aranet_relative_humidity",
                "df_name": "Humidity",
                "db_name": "humidity",
            },
        ],
    },
    {
        "readings_class": ReadingsAranetCO2Class,
        "sensor_type": CONST_ARANET_CO2_SENSOR_TYPE,
        "columns": [
            {"api_name": "aranet_co2", "df_name": "CO2", "db_name": "co2"},
        ],
    },
    {
        "readings_class": ReadingsAranetAirVelocityClass,
        "sensor_type": CONST_ARANET_AIRVELOCITY_SENSOR_TYPE,
        "columns": [
            {"api_name": "aranet_current", "df_name": "Current", "db_name": "current"},
            {
                "api_name": "aranet_current_derived",
                "df_name": "CurrentDerived",
                "db_name": "air_velocity",
            },
        ],
    },
    {
        "readings_class": ReadingsAegisIrrigationClass,
        "sensor_type": CONST_AEGIS_IRRIGATION_SENSOR_TYPE,
        "columns": [
            {
                "api_name": "aegis_ii_temperature",
                "df_name": "WaterTemperature",
                "db_name": "temperature",
            },
            {
                "api_name": "aegis_ii_ph",
                "df_name": "WaterPH",
                "db_name": "pH",
            },
            {
                "api_name": "aegis_ii_conductivity",
                "df_name": "WaterConductivity",
                "db_name": "conductivity",
            },
            {
                "api_name": "aegis_ii_disolved_oxygen",
                "df_name": "WaterOxygen",
                "db_name": "dissolved_oxygen",
            },
            {
                "api_name": "aegis_ii_turbidity_ntu",
                "df_name": "WaterTurbidity",
                "db_name": "turbidity",
            },
            {
                "api_name": "aegis_ii_peroxide",
                "df_name": "WaterPeroxide",
                "db_name": "peroxide",
            },
        ],
    },
]


def get_api_sensor_data(api_key, dt_from, dt_to, columns):
    """
    Makes a request to download sensor data for specified metrics for a specified period
    of time.  Note that this gets data for _all_ sensors, and returns it as a dict,
    keyed by Aranet id.

    Arguments:
        api_key: api key for authentication
        dt_from: date range from
        dt_to: date range to
        columns: list of dictionaries containing metric names, as defined in
        READINGS_DICTS
    Return:
        success: whether data request was succesful
        error: error message
        data_df_dict: dictionary of {aranet_pro_id (str): DataFrame of sensor_data}
    """
    success = True
    error = ""
    data_df_dict = {}

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    }

    dt_from_iso = dt_from.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    dt_to_iso = dt_to.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    url = CONST_CHECK_URL_PATH

    # get metrics as a single string, comma-separating each metric name
    metrics = ",".join([c["api_name"] for c in columns])
    params = {
        "start_time": dt_from_iso,
        "end_time": dt_to_iso,
        "metrics": metrics,
        "resolution": "10m",
        "metadata": "true",
    }
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        error = "Request's [%s] status code: %d" % (url[:70], response.status_code)
        success = False
        return success, error, data_df_dict
    # if we got to here, we have an API response for all sensors
    data = response.json()
    # the metadata contains a mapping between the Hyper id (MAC address) and the
    # aranet_pro_id
    device_mapping = data["metadata"]["devices"]
    timestamps = data["labels"]
    value_dicts = data["series"]
    for value_dict in value_dicts:
        hyper_id = value_dict["device_id"]
        aranet_pro_id = device_mapping[hyper_id]["vendor_device_id"]
        device_name = device_mapping[hyper_id]["name"]
        metric_name = value_dict["metric"]
        # TODO This is ad hoc, how do we do this more robustly?
        if "aegis" in device_name.lower():
            aranet_pro_id = "AegisII"
        # what if we don't have an aranet_pro_id for this sensor?
        if not aranet_pro_id:
            # it could be AegisII irrigation data
            if "aegis" in metric_name:
                aranet_pro_id = "AegisII"
            else:
                logging.info(f"No aranet pro id for sensor {hyper_id}")
                continue

        df_name = next(c["df_name"] for c in columns if c["api_name"] == metric_name)
        if aranet_pro_id not in data_df_dict:
            data_df = pd.DataFrame({"Timestamp": pd.to_datetime(timestamps)})
            data_df.set_index("Timestamp", inplace=True)
            data_df_dict[aranet_pro_id] = data_df
        else:
            data_df = data_df_dict[aranet_pro_id]
        data_df[df_name] = value_dict["values"]
        # put this DataFrame into a dict, keyed by the aranet id
        data_df_dict[aranet_pro_id] = data_df

    return success, error, data_df_dict


def _get_sensor_id_and_type(aranet_pro_id, engine):
    """Get the CROP sensor ID and sensor type from the CROP database, based on the
    Aranet Pro ID.
    """
    session = session_open(engine)
    query = session.query(SensorClass.id, TypeClass.sensor_type).filter(
        and_(
            SensorClass.aranet_pro_id == aranet_pro_id,
            SensorClass.type_id == TypeClass.id,
        )
    )
    result = session.execute(query).fetchone()
    if result is None:
        sensor_id, sensor_type = None, None
    else:
        sensor_id, sensor_type = result
    session_close(session)
    return sensor_id, sensor_type


def import_hyper_metric(
    engine, dt_from, dt_to, ReadingsClass, columns, sensor_type, conn_string
):
    """
    For each type of sensor, make a call to the Hyper API, get a corresponding
    dictionary of dataframes (keyed by the Aranet ID of the sensor), get the timestamps
    of existing readings in the database, and upload new readings.

    Arguments:
        engine: sqlalchemy engine, connected to the database
        dt_from: datetime
        dt_to: datetime,
        ReadingsClass: the SQLAlchemy class (from structure.py) corresponding to the
        sensor type
        columns: list of dicts, names of the columns as defined in READINGS_DICTS at top
        of module.
        sensor_type: str, only used for log message.
        conn_string: str, only used for log message.

    Returns:
        success: bool, did we successfully retrieve data from the API, the DB, and
        upload new data?
        error: str, any error messages that arose
    """
    # Create the readings table if it doesn't exist.
    try:
        ReadingsClass.__table__.create(bind=engine)
    except ProgrammingError:
        # The table already exists.
        pass

    logging.info(
        f"Requesting {sensor_type} data from {dt_from} to {dt_to} from the Hyper API"
    )
    success, error, hyper_data_dict = get_api_sensor_data(
        CONST_CROP_HYPER_APIKEY, dt_from, dt_to, columns
    )
    if not success:
        logging.info(error)
        return success, error

    # Write the data to the CROP database, sensor by sensor.
    for aranet_pro_id, api_data_df in hyper_data_dict.items():
        logging.info(f"Writing data for sensor with Aranet Pro ID {aranet_pro_id}")
        # Find the sensor_id that CROP uses for this sensor, and fetch existing data for
        # this sensor.
        sensor_id, this_sensor_type = _get_sensor_id_and_type(aranet_pro_id, engine)
        if sensor_id is None:
            logging.info(f"Sensor {aranet_pro_id} does not exist in the CROP database")
            continue
        if this_sensor_type != sensor_type:
            msg = (
                f"While requesting data for {sensor_type} sensors,"
                f" also received data for sensor {sensor_id}"
                f" that is of type {this_sensor_type}."
            )
            logging.warning(msg)
            continue

        session = session_open(engine)
        db_data_df = get_sensor_readings_db_timestamps(
            session,
            sensor_id,
            dt_from + timedelta(hours=-1),
            dt_to + timedelta(hours=1),
        )
        session_close(session)
        # From the data returned by Hyper, filter out all the data we already have.
        if len(db_data_df) > 0:
            api_index = api_data_df.index
            db_index = db_data_df.index.tz_localize(api_index.tz)
            new_data_df = api_data_df[~api_index.isin(db_index)]
        else:
            new_data_df = api_data_df
        new_data_df = new_data_df[~new_data_df.isna().any(axis=1)]
        if len(new_data_df) == 0:
            continue

        logging.info(f"Writing {len(new_data_df)} new readings")
        session = session_open(engine)
        # loop over all readings for this sensor.
        for idx, row in new_data_df.iterrows():
            new_reading = ReadingsClass(sensor_id=sensor_id, timestamp=idx)
            for column in columns:
                setattr(new_reading, column["db_name"], row[column["df_name"]])
            session.add(new_reading)
        # end of loop over readings - update the 'last_updated' column for the Sensor.
        session.query(SensorClass).filter(SensorClass.id == sensor_id).update(
            {"last_updated": datetime.utcnow()}
        )
        session_close(session)

        upload_log = "New: {} (uploaded);".format(len(new_data_df.index))
        log_upload_event(
            sensor_type,
            "Hyper API; Sensor ID {}".format(sensor_id),
            success,
            upload_log,
            conn_string,
        )

    return True, ""


def import_hyper_data(conn_string, database, dt_from, dt_to):
    """
    This is the main function for this module.
    Uploads data to the CROP database, for various metrics, from the Hyper.ag API.
    Uses the READINGS_DICTS defined at the top of this module to steer what metrics
    go into what table, and calls import_hyper_metric for every entry in that.

    Arguments:
        conn_string: connection string
        database: the name of the database
        dt_from: date range from
        dt_to: date range to
    Returns:
        status, error
    """
    # Create a CROP database connection to use.
    success, log, engine = connect_db(conn_string, database)
    if not success:
        logging.info(log)
        return success, log
    error = ""
    # loop through the different types of sensor, and call import_hyper_metric for each
    for readings_dict in READINGS_DICTS:
        logging.info("===> Importing data from {}".format(readings_dict["sensor_type"]))
        metric_success, metric_error = import_hyper_metric(
            engine,
            dt_from,
            dt_to,
            readings_dict["readings_class"],
            readings_dict["columns"],
            readings_dict["sensor_type"],
            conn_string,
        )
        success &= metric_success
        error += metric_error
    return success, error
