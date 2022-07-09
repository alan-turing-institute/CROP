"""
Analysis dashboards module.
"""

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

from utilities.utils import download_csv, parse_date_range_argument

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass,
    ReadingsAdvanticsysClass,
    ReadingsEnergyClass,
    ReadingsZensieTRHClass,
    ReadingsAranetTRHClass
)
from __app__.crop.constants import CONST_MAX_RECORDS, CONST_TIMESTAMP_FORMAT


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


def zensie_analysis(dt_from, dt_to):
    """
    Performs data analysis for Zensie sensors.

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
    Returns:
        sensor_names: a list of sensor names
        sensor_temp_ranges: json data with temperate ranges
    """

    logging.info(
        "Calling zensie_analysis with parameters %s %s"
        % (
            dt_from.strftime(CONST_TIMESTAMP_FORMAT),
            dt_to.strftime(CONST_TIMESTAMP_FORMAT),
        )
    )

    query = db.session.query(
        ReadingsZensieTRHClass.timestamp,
        ReadingsZensieTRHClass.sensor_id,
        SensorClass.name,
        ReadingsZensieTRHClass.temperature,
        ReadingsZensieTRHClass.humidity,
    ).filter(
        and_(
            ReadingsZensieTRHClass.sensor_id == SensorClass.id,
            ReadingsZensieTRHClass.timestamp >= dt_from,
            ReadingsZensieTRHClass.timestamp <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    logging.info("Total number of records found: %d" % (len(df.index)))
    return temperature_range_analysis(df, dt_from, dt_to)


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
    sensor_temp_ranges = {}

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


@blueprint.route("/advanticsys_dashboard")
@login_required
def advanticsys_dashboard():
    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))
    adv_sensors_temp = {}

    # advanticsys
    query = db.session.query(
        ReadingsAdvanticsysClass.timestamp,
        ReadingsAdvanticsysClass.sensor_id,
        SensorClass.id,
        ReadingsAdvanticsysClass.temperature,
        ReadingsAdvanticsysClass.humidity,
        ReadingsAdvanticsysClass.co2,
    ).filter(
        and_(
            ReadingsAdvanticsysClass.sensor_id == SensorClass.id,
            ReadingsAdvanticsysClass.timestamp >= dt_from,
            ReadingsAdvanticsysClass.timestamp <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    if not df.empty:

        # unique sensors
        adv_sensors = df.sensor_id.unique()
        print("advant", adv_sensors)
        adv_sensors_modbus_ids = df.id.unique()

        # extracting date from datetime
        df["date"] = pd.to_datetime(df["timestamp"].dt.date)

        # Reseting index
        df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

        # grouping data by date-hour and sensor id
        adv_grp = df.groupby(
            by=[
                df.timestamp.map(
                    lambda x: "%04d-%02d-%02d-%02d" % (x.year, x.month, x.day, x.hour)
                ),
                "sensor_id",
                "date",
            ]
        )

        # estimating hourly temperature mean values
        adv_grp_temp = adv_grp["temperature"].mean().reset_index()

        # binning temperature values
        adv_grp_temp["temp_bin"] = pd.cut(adv_grp_temp["temperature"], TEMP_BINS)

        # converting bins to str
        adv_grp_temp["temp_bin"] = adv_grp_temp["temp_bin"].astype(str)

        # get bin counts for each sensor-day combination
        adv_grp_date = adv_grp_temp.groupby(by=["sensor_id", "date", "temp_bin"])
        adv_cnt = adv_grp_date["temperature"].count().reset_index()
        adv_cnt.rename(columns={"temperature": "temp_cnt"}, inplace=True)

        json_data = []
        for adv_sensor_id in adv_sensors:

            adv_cnt_sensor = adv_cnt[adv_cnt["sensor_id"] == adv_sensor_id]

            del adv_cnt_sensor["sensor_id"]

            # Adding missing date/temp_bin combos
            bins_list, df_list = resample(adv_cnt_sensor, TEMP_BINS, dt_from, dt_to)

            bins_json = []

            for i, bin_range in enumerate(bins_list):
                temp_bin_df = df_list[i]
                temp_bin_df["date"] = pd.to_datetime(
                    temp_bin_df["date"], format="%Y-%m-%d"
                ).dt.strftime("%Y-%m-%d")

                bins_json.append(
                    '["'
                    + bin_range
                    + '",'
                    + temp_bin_df.to_json(orient="records")
                    + "]"
                )

            json_data.append("[" + ",".join(bins_json) + "]")

        adv_sensors_temp["data"] = "[" + ",".join(json_data) + "]"

    else:
        adv_sensors_modbus_ids = []

    return render_template(
        "advanticsys_dashboard.html",
        num_adv_sensors=len(adv_sensors_modbus_ids),
        adv_sensors=adv_sensors_modbus_ids,
        adv_sensors_temp=adv_sensors_temp,
        dt_from=dt_from.strftime("%B %d, %Y"),
        dt_to=dt_to.strftime("%B %d, %Y"),
    )


def fetch_zensie_data(dt_from, dt_to, sensor_ids):
    query = db.session.query(
        ReadingsZensieTRHClass.timestamp,
        ReadingsZensieTRHClass.sensor_id,
        SensorClass.name,
        ReadingsZensieTRHClass.temperature,
        ReadingsZensieTRHClass.humidity,
    ).filter(
        and_(
            ReadingsZensieTRHClass.sensor_id == SensorClass.id,
            ReadingsZensieTRHClass.timestamp >= dt_from,
            ReadingsZensieTRHClass.timestamp <= dt_to,
            ReadingsZensieTRHClass.sensor_id.in_(sensor_ids),
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)
    return df


@blueprint.route("/zensie_dashboard")
@login_required
def zensie_dashboard():
    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))
    num_zensie_sensors, temperature_bins_json = zensie_analysis(dt_from, dt_to)
    return render_template(
        "zensie_dashboard.html",
        num_zensie_sensors=num_zensie_sensors,
        temperature_bins_json=temperature_bins_json,
        dt_from=dt_from.strftime("%B %d, %Y"),
        dt_to=dt_to.strftime("%B %d, %Y"),
    )


def fetch_aranet_trh_data(dt_from, dt_to, sensor_ids):
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
            ReadingsAranetTRHClass.sensor_id.in_(sensor_ids),
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)
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


def format_sensor_ids_str(sensor_ids):
    if sensor_ids:
        return str(sensor_ids).replace("(", "").rstrip(" ,)")
    else:
        return ""


def add_mean_over_sensors(sensor_ids, df):
    """Take the dataframe for timeseries, and add data for a new "sensor" that's the
    mean of all the ones in the data
    """
    df_mean = df.groupby("timestamp").mean()
    df_mean.loc[:, "sensor_id"] = "mean"
    df_mean.loc[:, "name"] = "mean"
    # The sensor data comes with a 10 minute frequency. However, the sensors may be
    # "phase shifted" with respect to each other, e.g. one may have data for 00 and 10,
    # while another may have 05 and 15. A 10 minute rolling mean smooths out these
    # differences.
    roll_window = timedelta(minutes=10)
    for column_name in ("temperature", "humidity"):
        df_mean[column_name] = df_mean[column_name].rolling(roll_window).mean()
    df_mean = df_mean.reset_index()
    df = pd.concat((df_mean, df), axis=0)
    return df


@blueprint.route("/timeseries_dashboard", methods=["GET", "POST"])
@login_required
def timeseries_dashboard():
    # Read query string
    dt_from = request.args.get("startDate")
    dt_to = request.args.get("endDate")
    sensor_ids = request.args.get("sensorIds")
    if dt_from is None or dt_to is None or sensor_ids is None:
        today = datetime.today()
        dt_from = today - timedelta(days=1)
        dt_to = today
        return render_template(
            "timeseries_dashboard.html",
            sensor_ids=format_sensor_ids_str(sensor_ids),
            dt_from=dt_from,
            dt_to=dt_to,
            data=dict(),
            summaries=dict(),
        )

    # Convert strings to objects
    dt_from = datetime.strptime(dt_from, "%Y%m%d")
    # Make dt_to run to the end of the day in question.
    dt_to = (
        datetime.strptime(dt_to, "%Y%m%d")
        + timedelta(days=1)
        + timedelta(milliseconds=-1)
    )
    sensor_ids = tuple(map(int, re.split(r"[ ;,]+", sensor_ids.rstrip(" ,;"))))

    df = fetch_aranet_trh_data(dt_from, dt_to, sensor_ids)
    if request.method == "POST":
        return download_csv(df, "timeseries")

    data_keys = list(sensor_ids)
    if len(sensor_ids) > 1:
        df = add_mean_over_sensors(sensor_ids, df)
        # Insert at start, to make "mean" be the first one displayed on the page.
        data_keys.insert(0, "mean")

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
        summary_dict[key] = json.loads(df_key.describe().to_json())
    return render_template(
        "timeseries_dashboard.html",
        sensor_ids=format_sensor_ids_str(sensor_ids),
        dt_from=dt_from,
        dt_to=dt_to,
        data=data_dict,
        summaries=summary_dict,
    )
