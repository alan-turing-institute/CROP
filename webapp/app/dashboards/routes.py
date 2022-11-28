"""
Analysis dashboards module.
"""

try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable
import copy
from datetime import datetime, timedelta
import json
import logging
import re

import numpy as np
import pandas as pd

from flask_login import login_required
from flask import render_template, request
from sqlalchemy import and_

from app.dashboards import blueprint

from core import queries
from core.utils import (
    download_csv,
    parse_date_range_argument,
    query_result_to_array,
)

from core.structure import SQLA as db
from core.structure import (
    SensorClass,
    TypeClass,
    ReadingsAegisIrrigationClass,
    ReadingsEnergyClass,
    ReadingsAranetCO2Class,
    ReadingsAranetTRHClass,
    ReadingsAranetAirVelocityClass,
)
from core.constants import CONST_MAX_RECORDS, CONST_TIMESTAMP_FORMAT


# Temperature constants
TEMP_BINS = {
    "Propagation": [0.0, 20.0, 23.0, 25.0, 144.0],
    "FrontFarm": [0.0, 18.0, 21.0, 25.0, 144.0],
    "Fridge": [0.0, 20.0, 23.0, 25.0, 144.0],
    "MidFarm": [0.0, 20.0, 23.0, 25.0, 144.0],
    "BackFarm": [0.0, 20.0, 25.0, 28.0, 144.0],
    "Tunnel": [0.0, 20.0, 25.0, 28.0, 144.0],
    "R&D": [0.0, 20.0, 23.0, 25.0, 144.0],
}
# TODO Read these from the database.
SENSOR_CATEORIES = {
    18: "MidFarm",
    19: "Tunnel",
    20: "Propagation",
    21: "FrontFarm",
    22: "BackFarm",
    23: "MidFarm",
    24: "R&D",
    25: "R&D",
    26: "Fridge",
    27: "MidFarm",
    48: "Propagation",
    49: "R&D",
}

# Ventilation constants
CONST_SFP = 2.39  # specific fan power
CONST_VTOT = 20337.0  # total volume – m3

DEFAULT_SENSOR_TYPE = "Aranet T&RH"

# Some data that varies based on sensor type.
# DATA_COLUMNS_BY_SENSOR_TYPE names the class for the readings table.
DATA_TABLES_BY_SENSOR_TYPE = {
    "Aranet T&RH": lambda: queries.trh_with_vpd(db.session).subquery().c,
    "Aranet CO2": lambda: ReadingsAranetCO2Class,
    "Aranet Air Velocity": lambda: ReadingsAranetAirVelocityClass,
    "Aegis II": lambda: ReadingsAegisIrrigationClass,
}
# DATA_COLUMNS_BY_SENSOR_TYPE names the columns of that table that we want to plot as
# data, and gives them human friendly names to display on the UI.
# TODO Could the below data be read from the database?
DATA_COLUMNS_BY_SENSOR_TYPE = {
    "Aranet T&RH": [
        {"column_name": "temperature", "ui_name": "Temperature (°C)"},
        {"column_name": "humidity", "ui_name": "Humidity (%)"},
        {"column_name": "vpd", "ui_name": "VPD (Pa)"},
    ],
    "Aranet CO2": [
        {"column_name": "co2", "ui_name": "CO2 (ppm)"},
    ],
    "Aranet Air Velocity": [
        {"column_name": "air_velocity", "ui_name": "Air velocity (m/s)"},
    ],
    "Aegis II": [
        {"column_name": "temperature", "ui_name": "Temperature (°C)"},
        {"column_name": "pH", "ui_name": "pH"},
        {"column_name": "dissolved_oxygen", "ui_name": "Dissolved oxygen (%)"},
        {"column_name": "conductivity", "ui_name": "Conductivity (μS)"},
        {"column_name": "turbidity", "ui_name": "Turbidity"},
        {"column_name": "peroxide", "ui_name": "Peroxide (ppm)"},
    ],
}

# The above constants are defined in terms of names of the sensor_types. The code
# operates in terms of ids rather than names, so we wrap the above dictionaries into
# functions.


def get_sensor_type_name(sensor_type_id):
    """Given a sensor type ID, get the name of the sensor type from the database."""
    query = db.session.query(
        TypeClass.sensor_type,
    ).filter(TypeClass.id == sensor_type_id)
    sensor_name = db.session.execute(query).fetchone()
    if isinstance(sensor_name, Iterable):
        sensor_name = sensor_name[0]
    return sensor_name


def get_sensor_type_id(sensor_type_name):
    """Given a sensor type name, get the ID of the sensor type from the database."""
    query = db.session.query(
        TypeClass.id,
    ).filter(TypeClass.sensor_type == sensor_type_name)
    sensor_id = db.session.execute(query).fetchone()
    if isinstance(sensor_id, Iterable):
        sensor_id = sensor_id[0]
    return sensor_id


def get_table_by_sensor_type(sensor_type_id):
    """Return the SQLAlchemy table/subquery corresponding to a given sensor type ID."""
    # Because of how global constants work in Flask, DATA_COLUMNS_BY_SENSOR_TYPE has
    # functions that return the relevant table/subquery, rather than the
    # tables/subqueries themselves. Hence the calls like `value()` and setting
    # `value = lambda: None`
    global DATA_TABLES_BY_SENSOR_TYPE
    if sensor_type_id in DATA_TABLES_BY_SENSOR_TYPE:
        return DATA_TABLES_BY_SENSOR_TYPE[sensor_type_id]()
    else:
        sensor_type_name = get_sensor_type_name(sensor_type_id)
        if sensor_type_name in DATA_TABLES_BY_SENSOR_TYPE:
            value = DATA_TABLES_BY_SENSOR_TYPE[sensor_type_name]
        else:
            value = lambda: None
        DATA_TABLES_BY_SENSOR_TYPE[sensor_type_id] = value
        return value()


def get_columns_by_sensor_type(sensor_type_id):
    """Return the names of the data columns in the table corresponding to a given sensor
    type ID.

    By "data columns" we mean the ones that depend on the sensor type and hold the
    actual data, e.g. temperature and humidity, but not timestamp. The return values are
    dictionaries with two keys, "column_name" for the name by which the database knows
    this column, and "ui_name" for nice human-readable name fit for a UI.
    """
    global DATA_COLUMNS_BY_SENSOR_TYPE
    if sensor_type_id in DATA_COLUMNS_BY_SENSOR_TYPE:
        return DATA_COLUMNS_BY_SENSOR_TYPE[sensor_type_id]
    else:
        sensor_type_name = get_sensor_type_name(sensor_type_id)
        if sensor_type_name in DATA_COLUMNS_BY_SENSOR_TYPE:
            value = DATA_COLUMNS_BY_SENSOR_TYPE[sensor_type_name]
        else:
            value = None
        DATA_COLUMNS_BY_SENSOR_TYPE[sensor_type_id] = value
        return value


def get_default_sensor_type():
    """Get the ID of the default sensor type."""
    return get_sensor_type_id(DEFAULT_SENSOR_TYPE)


def is_valid_sensor_type(sensor_type_id):
    """Return True if we have the necessary metadata about the table and its columns
    needed for fetching and plotting data for the given sensor type, otherwise False.
    """
    return (
        get_table_by_sensor_type(sensor_type_id) is not None
        and get_columns_by_sensor_type(sensor_type_id) is not None
    )


# # # DONE WITH GLOBAL CONSTANTS AND SENSOR TYPE METADATA, BEGIN MAIN CONTENT # # #


def resample(df, bins, dt_from, dt_to):
    """
    Resamples (adds missing date/temperature bin combinations) to a dataframe.

    Arguments:
        df: dataframe with temperature assign to bins
        bins: temperature bins as a list
        dt_from: date range from
        dt_to: date range to
    Returns:
        bins_list: a list of temperature bins
        df_list: a list of df corresponding to temperature bins
    """

    bins_list = []
    for i in range(len(bins) - 1):
        bins_list.append("(%.1f, %.1f]" % (bins[i], bins[i + 1]))

    date_min = min(df["date"].min(), dt_from)
    date_max = max(df["date"].max(), dt_to)

    for n in range(int((date_max - date_min).days) + 1):
        day = date_min + timedelta(n)

        for temp_range in bins_list:
            if len(df[(df["date"] == day) & (df["temp_bin"] == temp_range)].index) == 0:

                df2 = pd.DataFrame(
                    {"date": [day], "temp_bin": [temp_range], "temp_cnt": [0]}
                )

                df = df.append(df2)

    df = df.sort_values(by=["date", "temp_bin"], ascending=True)

    df.reset_index(inplace=True, drop=True)

    df_list = []

    for bin_range in bins_list:

        df_bin = df[df["temp_bin"] == bin_range]

        del df_bin["temp_bin"]

        df_bin.reset_index(inplace=True, drop=True)

        df_list.append(df_bin)

    return bins_list, df_list


def lights_energy_use(dt_from_, dt_to_):
    """
    Energy use from Carpenter's place (with lights - called Clapham in the database)

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
    Returns:
        lights_results_df - a pandas dataframe with mean lights on values
    """

    dt_from = pd.to_datetime(dt_from_.date()) + timedelta(hours=14)
    dt_to = pd.to_datetime(dt_to_.date()) + timedelta(days=1, hours=15)

    d_from = pd.to_datetime(dt_from_.date())
    d_to = pd.to_datetime(dt_to_.date())

    col_ec = "electricity_consumption"
    sensor_device_id = "Clapham"
    lights_on_cols = []

    # getting eneregy data for the analysis
    query = db.session.query(
        ReadingsEnergyClass.timestamp,
        ReadingsEnergyClass.electricity_consumption,
    ).filter(
        and_(
            SensorClass.device_id == sensor_device_id,
            ReadingsEnergyClass.sensor_id == SensorClass.id,
            ReadingsEnergyClass.timestamp >= dt_from,
            ReadingsEnergyClass.timestamp <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    if df.empty:
        return pd.DataFrame({"date": [], "mean_lights_on": []})

    # Reseting index
    df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    # grouping data by date-hour
    energy_hour = (
        df.groupby(
            by=[
                df["timestamp"].map(
                    lambda x: pd.to_datetime(
                        "%04d-%02d-%02d-%02d" % (x.year, x.month, x.day, x.hour),
                        format="%Y-%m-%d-%H",
                    )
                ),
            ]
        )["electricity_consumption"]
        .sum()
        .reset_index()
    )

    # Sorting and reseting index
    energy_hour.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    # energy dates. Energy date starts from 4pm each day and lasts for 24 hours
    energy_hour.loc[
        energy_hour["timestamp"].dt.hour < 15, "energy_date"
    ] = pd.to_datetime((energy_hour["timestamp"] + timedelta(days=-1)).dt.date)
    energy_hour.loc[
        energy_hour["timestamp"].dt.hour >= 15, "energy_date"
    ] = pd.to_datetime(energy_hour["timestamp"].dt.date)

    # Clasification of lights being on

    # Lights ON 1: Lights turn on at 4pm and turn off at 9am, as scheduled.
    energy_hour["lights_on_1"] = energy_hour["timestamp"].apply(
        lambda x: 1 if (x.hour >= 17 or x.hour < 10) else 0
    )
    lights_on_cols.append("lights_on_1")

    # Lights ON 2: Lights are calculated by estimating the lighting use as between
    #   the minima of two consecutive days. The lights are considered on when the
    #   energy use is above the day's first quartile of lighting of this difference.
    # energy_hour['lights_on_2'] = 0
    # lights_on_cols.append('lights_on_2')

    # Lights ON 3: Lights are assumed to be on if the energy demand is over 30 kW
    #   (max load of the extraction fan)
    energy_hour["lights_on_3"] = energy_hour[col_ec].apply(
        lambda x: 1 if (x > 30.0) else 0
    )
    lights_on_cols.append("lights_on_3")

    # Lights ON 4: Lights are assumed to turn on at the time of largest energy use
    #   increase in the day, and turn off at the time of largest energy decrease of
    #   the day.

    # estimating energy difference
    energy_hour["dE"] = energy_hour[col_ec] - energy_hour[col_ec].shift(1)
    energy_hour["dE"] = energy_hour["dE"].fillna(0.0)

    # finding max increase and min decrease
    energy_hour["dE_min"] = energy_hour.groupby("energy_date")["dE"].transform("min")
    energy_hour["dE_max"] = energy_hour.groupby("energy_date")["dE"].transform("max")

    energy_hour.loc[
        np.isclose(energy_hour["dE_max"], energy_hour["dE"]), "lights_on_4"
    ] = 1
    energy_hour.loc[
        np.isclose(energy_hour["dE_min"], energy_hour["dE"]), "lights_on_4"
    ] = 0

    # repeat last?
    prev_row_value = None
    for df_index in energy_hour.index:
        if df_index > 0:
            if np.isnan(energy_hour.loc[df_index, "lights_on_4"]) and not np.isnan(
                prev_row_value
            ):

                energy_hour.loc[df_index, "lights_on_4"] = prev_row_value
        prev_row_value = energy_hour.loc[df_index, "lights_on_4"]

    lights_on_cols.append("lights_on_4")

    # Lights ON 5: Lights are assumed on if the energy use is over 0.9
    #   times the days' energy use mean, and the energy demand is over 30 kW.

    energy_hour["energy_date_mean"] = energy_hour.groupby("energy_date")[
        col_ec
    ].transform("mean")

    energy_hour["lights_on_5"] = np.where(
        (energy_hour[col_ec] > 30.0)
        & (energy_hour[col_ec] > 0.9 * energy_hour["energy_date_mean"]),
        1,
        0,
    )

    lights_on_cols.append("lights_on_5")

    # getting the mean value of lights on per day
    energy_date_df = energy_hour.loc[
        (energy_hour["energy_date"] >= d_from) & (energy_hour["energy_date"] <= d_to)
    ]
    energy_date_df = (
        energy_date_df.groupby(by=["energy_date"])[lights_on_cols].sum().reset_index()
    )
    energy_date_df["mean_lights_on"] = energy_date_df[lights_on_cols].sum(axis=1) / len(
        lights_on_cols
    )
    energy_date_df["date"] = energy_date_df["energy_date"].dt.strftime("%Y-%m-%d")

    lights_results_df = energy_date_df[["date", "mean_lights_on"]]

    return lights_results_df


def ventilation_energy_use(dt_from, dt_to):
    """
    In our data this is called Carpenter’s Place. This reading only counts energy use for
        the second extraction fan.

    Arguments:
        dt_from: date range from
        dt_to: date range to
    Returns:
        ventilation_results_df - a pandas dataframe with ventilation analysis results
    """
    sensor_device_id = "1a Carpenters Place"

    # getting eneregy data for the analysis
    query = db.session.query(
        ReadingsEnergyClass.timestamp,
        ReadingsEnergyClass.electricity_consumption,
    ).filter(
        and_(
            SensorClass.device_id == sensor_device_id,
            ReadingsEnergyClass.sensor_id == SensorClass.id,
            ReadingsEnergyClass.timestamp >= dt_from,
            ReadingsEnergyClass.timestamp <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    if df.empty:
        return pd.DataFrame({"timestamp": [], "ach": []})

    # Reseting index
    df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    # grouping data by date-hour
    energy_hour = (
        df.groupby(
            by=[
                df["timestamp"].map(
                    lambda x: "%04d-%02d-%02d %02d:00"
                    % (x.year, x.month, x.day, x.hour)
                ),
            ]
        )["electricity_consumption"]
        .sum()
        .reset_index()
    )

    # Sorting and reseting index
    energy_hour.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    # Calculating air exchange per hour
    energy_hour["ach"] = (
        energy_hour["electricity_consumption"] / CONST_SFP * 3600.0 / (CONST_VTOT / 2.0)
    )

    ventilation_results_df = energy_hour[["timestamp", "ach"]]

    return ventilation_results_df


def aranet_trh_analysis(dt_from, dt_to):
    """
    Performs data analysis for Aranet Temperature+Relative Humidity sensors.

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
    Returns:
        sensor_names: a list of sensor names
        sensor_temp_ranges: json data with temperate ranges
    """

    logging.info(
        "Calling aranet_trh_analysis with parameters %s %s"
        % (
            dt_from.strftime(CONST_TIMESTAMP_FORMAT),
            dt_to.strftime(CONST_TIMESTAMP_FORMAT),
        )
    )

    query = db.session.query(
        ReadingsAranetTRHClass.timestamp,
        ReadingsAranetTRHClass.sensor_id,
        SensorClass.name,
        ReadingsAranetTRHClass.temperature,
        ReadingsAranetTRHClass.humidity,
    ).filter(
        and_(
            ReadingsAranetTRHClass.sensor_id == SensorClass.id,
            ReadingsAranetTRHClass.timestamp >= dt_from,
            ReadingsAranetTRHClass.timestamp <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    logging.info("Total number of records found: %d" % (len(df.index)))
    return temperature_range_analysis(df, dt_from, dt_to)


def temperature_range_analysis(temp_df, dt_from, dt_to):
    """
    Performs temperature range analysis on a given pandas dataframe.

    Arguments:
        temp_df:
        dt_from: date range from
        dt_to: date range to
    Returns:
        sensor_names: a list of sensor names
        sensor_temp_ranges: json data with temperate ranges
    """
    df = copy.deepcopy(temp_df)

    df_unique_sensors = df[["sensor_id", "name"]].drop_duplicates(["sensor_id", "name"])

    sensor_ids = df_unique_sensors["sensor_id"].tolist()
    sensor_names = df_unique_sensors["name"].tolist()

    # extracting date from datetime
    df["date"] = pd.to_datetime(df["timestamp"].dt.date)

    # Reseting index
    df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    data_by_sensor_id = {}
    for sensor_name, sensor_id in zip(sensor_names, sensor_ids):
        df_sensor = df[df["sensor_id"] == sensor_id]
        # grouping data by date-hour and sensor id
        sensor_grp = df_sensor.groupby(
            by=[
                df_sensor.timestamp.map(
                    lambda x: "%04d-%02d-%02d-%02d" % (x.year, x.month, x.day, x.hour)
                ),
                "date",
            ]
        )

        # estimating hourly temperature mean values
        sensor_grp_temp = sensor_grp["temperature"].mean().reset_index()

        try:
            bins = TEMP_BINS[SENSOR_CATEORIES[sensor_id]]
        except KeyError:
            logging.error(
                f"Don't know how to categorise or bin sensor {sensor_id} "
                "in the dashboard."
            )
            continue
        # binning temperature values
        sensor_grp_temp["temp_bin"] = pd.cut(sensor_grp_temp["temperature"], bins)

        # converting bins to str
        sensor_grp_temp["temp_bin"] = sensor_grp_temp["temp_bin"].astype(str)

        # get bin counts for each sensor-day combination
        sensor_grp_date = sensor_grp_temp.groupby(by=["date", "temp_bin"])

        sensor_cnt = sensor_grp_date["temperature"].count().reset_index()
        sensor_cnt.rename(columns={"temperature": "temp_cnt"}, inplace=True)

        # Adding missing date/temp_bin combos
        bins_list, df_list = resample(sensor_cnt, bins, dt_from, dt_to)

        data_by_sensor_id[sensor_id] = {
            "name": sensor_name,
            "bins": bins_list,
            "data": [
                {
                    "date": df["date"].dt.strftime("%Y-%m-%d").to_list(),
                    "count": df["temp_cnt"].to_list(),
                }
                for df in df_list
            ],
        }
    return len(data_by_sensor_id.keys()), json.dumps(data_by_sensor_id)


def fetch_sensor_data(dt_from, dt_to, sensor_type, sensor_ids):
    sensor_type_name = get_sensor_type_name(sensor_type)
    if not is_valid_sensor_type(sensor_type):
        raise ValueError(f"Don't know how to fetch data for sensor type {sensor_type}")
    data_table = get_table_by_sensor_type(sensor_type)
    data_table_columns = [
        getattr(data_table, column["column_name"])
        for column in get_columns_by_sensor_type(sensor_type)
    ]
    query = db.session.query(
        data_table.timestamp,
        data_table.sensor_id,
        SensorClass.name,
        *data_table_columns,
    ).filter(
        and_(
            data_table.sensor_id == SensorClass.id,
            data_table.timestamp >= dt_from,
            data_table.timestamp <= dt_to,
            data_table.sensor_id.in_(sensor_ids),
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)
    if sensor_type_name == "Aranet T&RH":
        # Rounding to two decimal places, because our precision isn't infinite, and
        # long floats look really ugly on the front end.
        df.loc[:, "vpd"] = df.loc[:, "vpd"].round(2)
    return df


@blueprint.route("/aranet_trh_dashboard")
@login_required
def aranet_trh_dashboard():
    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))
    num_sensors, temperature_bins_json = aranet_trh_analysis(dt_from, dt_to)
    return render_template(
        "aranet_trh_dashboard.html",
        num_sensors=num_sensors,
        temperature_bins_json=temperature_bins_json,
        dt_from=dt_from.strftime("%B %d, %Y"),
        dt_to=dt_to.strftime("%B %d, %Y"),
    )


@blueprint.route("/energy_dashboard")
@login_required
def energy_dashboard():
    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))
    energy_data = {}

    # lights-on analysis
    lights_results_df = lights_energy_use(dt_from, dt_to)

    # ventilation analysis
    ventilation_results_df = ventilation_energy_use(dt_from, dt_to)

    # jsonify
    energy_data["data"] = (
        "["
        + lights_results_df.to_json(orient="records")
        + ","
        + ventilation_results_df.to_json(orient="records")
        + "]"
    )

    return render_template(
        "energy_dashboard.html",
        energy_data=energy_data,
        dt_from=dt_from.strftime("%B %d, %Y"),
        dt_to=dt_to.strftime("%B %d, %Y"),
    )


# # # TIMESERIES DASHBOARD # # #


def add_mean_over_sensors(sensor_type, sensor_ids, df, roll_window_minutes=10):
    """Take the dataframe for timeseries, and add data for a new "sensor" that's the
    mean of all the ones in the data
    """
    if len(df) == 0:
        return df
    df_mean = df.groupby("timestamp").mean()
    df_mean.loc[:, "sensor_id"] = "mean"
    df_mean.loc[:, "name"] = "mean"
    # The sensor data comes with a 10 minute frequency. However, the sensors may be
    # "phase shifted" with respect to each other, e.g. one may have data for 00 and 10,
    # while another may have 05 and 15. A 10 minute rolling mean smooths out these
    # differences.
    roll_window = timedelta(minutes=roll_window_minutes)
    for column in get_columns_by_sensor_type(sensor_type):
        column_name = column["column_name"]
        df_mean[column_name] = df_mean[column_name].rolling(roll_window).mean()
    df_mean = df_mean.reset_index()
    df = pd.concat((df_mean, df), axis=0)
    return df


def fetch_all_sensor_types():
    """Get all sensor types from the CROP database, for which we know how to render the
    timeseries dashboard.

    Arguments:
        None
    Returns:
        List of dictionaries with keys "id" (int) and "sensor_type" (str).
    """
    query = db.session.query(
        TypeClass.id,
        TypeClass.sensor_type,
    )
    sensor_types = db.session.execute(query).fetchall()
    sensor_types = query_result_to_array(sensor_types)
    sensor_types = [st for st in sensor_types if is_valid_sensor_type(st["id"])]
    return sensor_types


def fetch_all_sensors(sensor_type):
    """Get all sensors of a given sensor type from the CROP database.

    Arguments:
        sensor_type: The database ID (primary key) of the sensor type.
    Returns:
        List of dictionaries with keys "id" (int) and "name" (str), sorted by "id".
    """
    query = db.session.query(
        SensorClass.id,
        SensorClass.aranet_code,
        SensorClass.name,
    ).filter(SensorClass.type_id == sensor_type)
    sensors = db.session.execute(query).fetchall()
    sensors = query_result_to_array(sensors)
    sensors = {s["id"]: s for s in sorted(sensors, key=lambda x: x["id"])}
    return sensors


@blueprint.route("/timeseries_dashboard", methods=["GET", "POST"])
@login_required
def timeseries_dashboard():
    # Read query string
    dt_from = request.args.get("startDate")
    dt_to = request.args.get("endDate")
    sensor_ids = request.args.get("sensorIds")
    if sensor_ids is not None:
        # sensor_ids is passed as a comma-separated (or space or semicolon, although
        # those aren't currently used) string of ints, split it into a list of ints.
        sensor_ids = tuple(map(int, re.split(r"[ ;,]+", sensor_ids.rstrip(" ,;"))))
    sensor_type = request.args.get("sensorType")
    if sensor_type is None:
        sensor_type = get_default_sensor_type()
    else:
        sensor_type = int(sensor_type)
    # Get the data from the database that will be required in all scenarios for how the
    # page might be rendered.
    sensor_types = fetch_all_sensor_types()
    all_sensors = fetch_all_sensors(sensor_type)

    # If we don't have the information necessary to plot data for sensors, just render
    # the selector version of the page.
    if (
        dt_from is None
        or dt_to is None
        or sensor_ids is None
        or not is_valid_sensor_type(sensor_type)
    ):
        today = datetime.today()
        dt_from = today - timedelta(days=7)
        dt_to = today
        return render_template(
            "timeseries_dashboard.html",
            sensor_type=sensor_type,
            sensor_types=sensor_types,
            all_sensors=all_sensors,
            sensor_ids=sensor_ids,
            dt_from=dt_from,
            dt_to=dt_to,
            data=dict(),
            summaries=dict(),
            data_columns=[],
        )

    # Convert datetime strings to objects and make dt_to run to the end of the day in
    # question.
    dt_from = datetime.strptime(dt_from, "%Y%m%d")
    dt_to = (
        datetime.strptime(dt_to, "%Y%m%d")
        + timedelta(days=1)
        + timedelta(milliseconds=-1)
    )

    df = fetch_sensor_data(dt_from, dt_to, sensor_type, sensor_ids)
    if request.method == "POST":
        df = df.sort_values("timestamp")
        return download_csv(df, "timeseries")

    data_keys = list(sensor_ids)
    if len(sensor_ids) > 1:
        df = add_mean_over_sensors(sensor_type, sensor_ids, df)
        # Insert at start, to make "mean" be the first one displayed on the page.
        data_keys.insert(0, "mean")

    data_columns = get_columns_by_sensor_type(sensor_type)
    data_dict = dict()
    summary_dict = dict()
    for key in data_keys:
        df_key = (
            df[df["sensor_id"] == key]
            .drop(columns=["sensor_id", "name"])
            .sort_values("timestamp")
        )
        # You may wonder, why we first to_json, and then json.loads. That's just to have
        # the data in a nice nested dictionary that a final json.dumps can deal with.
        data_dict[key] = json.loads(df_key.to_json(orient="records", date_format="iso"))
        # Round the summary stats to two decimals, for nice front end presentation.
        summary_dict[key] = json.loads(df_key.describe().round(2).to_json())
    return render_template(
        "timeseries_dashboard.html",
        sensor_type=sensor_type,
        sensor_types=sensor_types,
        all_sensors=all_sensors,
        sensor_ids=sensor_ids,
        dt_from=dt_from,
        dt_to=dt_to,
        data=data_dict,
        summaries=summary_dict,
        data_columns=data_columns,
    )
