from app.home import blueprint
from flask import render_template, request
from flask_login import login_required
from sqlalchemy import and_

import copy

import datetime as dt

import numpy as np
import pandas as pd
import json

import logging


from utilities.utils import parse_date_range_argument

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass,
    LocationClass,
    SensorLocationClass,
    ReadingsZensieTRHClass,
)
from __app__.crop.constants import CONST_MAX_RECORDS, CONST_TIMESTAMP_FORMAT


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

    for temp_range in bins_list:
        if len(df[(df["temp_bin"] == temp_range)].index) == 0:

            df2 = pd.DataFrame({"temp_bin": [temp_range], "temp_cnt": [0]})

            df = df.append(df2)

    df = df.sort_values(by=["temp_bin"], ascending=True)

    df.reset_index(inplace=True, drop=True)

    df_list = []

    for bin_range in bins_list:

        df_bin = df[df["temp_bin"] == bin_range]

        del df_bin["temp_bin"]

        df_bin.reset_index(inplace=True, drop=True)

        df_list.append(df_bin)

    return bins_list, df_list, df


# def weekly_calc (resampled_df_list):


def zensie_query(
    dt_from,
    dt_to,
):
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
        # SensorClass.name,
        ReadingsZensieTRHClass.temperature,
        ReadingsZensieTRHClass.humidity,
        # SensorLocationClass.location_id,
        LocationClass.zone,
    ).filter(
        and_(
            SensorLocationClass.location_id == LocationClass.id,
            ReadingsZensieTRHClass.sensor_id == SensorClass.id,
            ReadingsZensieTRHClass.sensor_id == SensorLocationClass.sensor_id,
            ReadingsZensieTRHClass.timestamp >= dt_from,
            ReadingsZensieTRHClass.timestamp <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    logging.info("Total number of records found: %d" % (len(df.index)))

    if not df.empty:
        # sensor_names = "mods"
        # sensor_temp_ranges = "meh"
        # sensor_temp_ranges = df.values[0]
        location_ids, sensor_temp_ranges = temperature_range_analysis(
            df, dt_from, dt_to
        )
        df_mean_hr = mean_sensor_values_per_hr(df)

    else:
        location_ids = []
        sensor_temp_ranges = {}

    return location_ids, sensor_temp_ranges, df_mean_hr


def mean_sensor_values_per_hr(temp_df):
    """
    finds mean of values per hour for a selected date.
    Returns a dataframe ready for json

    Arguments:
        temp_df:
        dt_from: date range from
        dt_to: date range to
    Returns:
        sensor_names: a list of sensor names
        sensor_temp_ranges: json data with temperate ranges
    """

    df = copy.deepcopy(temp_df)

    # extracting date from datetime
    df["date"] = pd.to_datetime(df["timestamp"].dt.date)

    # Reseting index
    df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    df_grp_zone_hr = (
        df.groupby(
            by=[
                df.timestamp.map(
                    lambda x: "%04d-%02d-%02d-%02d" % (x.year, x.month, x.day, x.hour)
                ),
                "zone",
                "date",
            ]
        )
        .mean()
        .reset_index()
    )

    return df_grp_zone_hr


# Temperature constants
TEMP_BINS = [0.0, 17.0, 21.0, 24.0, 30.0]


def temperature_analysis1(df, dt_from, dt_to):

    df_unique_zones = df[["zone"]].drop_duplicates(["zone"])
    location_zones = df_unique_zones["zone"].tolist()
    # sensor_grp_temp = zone_hr_grp["temperature"].mean().reset_index()

    TEMP_BINS = {
        "Propagation": [0.0, 20.0, 23.0, 25.0, 35.0],  # optimal 23
        "FrontFarm": [0.0, 18.0, 21.0, 25.0, 35.0],  # optimal 21
        "Fridge": [0.0, 20.0, 23.0, 25.0, 35.0],  # optimal 23
        "MidFarm": [0.0, 20.0, 23.0, 25.0, 35.0],  # optimal 23
        "BackFarm": [0.0, 20.0, 25.0, 28.0, 35.0],  # optimal 25
        "R&D": [0.0, 20.0, 23.0, 25.0, 35.0],  # optimal 23
    }
    HUM_BINS = [0.0, 50.0, 65.0, 75.0, 85.0]  # optimal 70
    temp_list = []

    for zone in location_zones:

        df_each_zone = df[df.zone == zone]
        # breaks df in temperature bins
        df_each_zone["temp_bin"] = pd.cut(df_each_zone["temperature"], TEMP_BINS[zone])
        # df_each_zone["hum_bin"] = pd.cut(df_each_zone["humidity"], HUM_BINS)

        # converting bins to str
        df_each_zone["temp_bin"] = df_each_zone["temp_bin"].astype(str)
        # df_each_zone["hum_bin"] = df_each_zone["hum_bin"].astype(str)

        # groups df per each bin
        bin_grp = df_each_zone.groupby(by=["zone", "temp_bin"])

        # get temperature counts per bin
        bin_cnt = bin_grp["temperature"].count().reset_index()

        # renames column with counts
        bin_cnt.rename(columns={"temperature": "temp_cnt"}, inplace=True)

        bins_list, df_list, df_ = resample(bin_cnt, TEMP_BINS[zone], dt_from, dt_to)
        df_["zone"] = zone

        temp_list.append(df_)
    df_merged = pd.concat(temp_list)  # merges all df in one.

    return df_merged
    ##########################


def temperature_range_analysis(temp_df, dt_from, dt_to):
    """
    Performs temperage range analysis on a given pandas dataframe.

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
    # print(df.head(10))

    df_unique_zones = df[["zone"]].drop_duplicates(["zone"])

    location_zones = df_unique_zones["zone"].tolist()

    # extracting date from datetime
    df["date"] = pd.to_datetime(df["timestamp"].dt.date)

    # Reseting index
    df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    # df.to_csv(
    #    r"C:\Users\Flora\OneDrive - The Alan Turing Institute\Turing\1.Projects\2.UrbanAgriculture\export_dataframe.csv",
    #    index=False,
    #    header=True,
    # )

    # grouping data by location zone
    sensor_grp = df.groupby(
        by=[
            df.timestamp.map(
                lambda x: "%04d-%02d-%02d-%02d" % (x.year, x.month, x.day, x.hour)
            ),
            "zone",
            "date",
        ]
    )

    zone_hr_grp = (
        df.groupby(
            by=[
                df.timestamp.map(
                    lambda x: "%04d-%02d-%02d-%02d" % (x.year, x.month, x.day, x.hour)
                ),
                "zone",
                "date",
            ]
        )
        .mean()
        .reset_index()
    )

    ###################
    Propagation_df = zone_hr_grp[zone_hr_grp.zone == "Propagation"]

    Propagation_df["temp_bin"] = pd.cut(Propagation_df["temperature"], TEMP_BINS)

    # converting bins to str
    Propagation_df["temp_bin"] = Propagation_df["temp_bin"].astype(str)

    # get bin counts for each sensor-day combination
    Propagation_grp = Propagation_df.groupby(by=["zone", "temp_bin"])
    temp_cnt = Propagation_grp["temperature"].count().reset_index()

    temp_cnt.rename(columns={"temperature": "temp_cnt"}, inplace=True)

    bins_list, df_list, df_ = resample(temp_cnt, TEMP_BINS, dt_from, dt_to)

    # print(df_list)
    ##########################
    # estimating hourly temperature mean values
    sensor_grp_temp = sensor_grp["temperature"].mean().reset_index()
    # print(sensor_grp_temp)

    # estimating hourly humidity mean values
    sensor_grp_hum = sensor_grp["humidity"].mean().reset_index()

    # binning temperature values
    sensor_grp_temp["temp_bin"] = pd.cut(sensor_grp_temp["temperature"], TEMP_BINS)

    # converting bins to str
    sensor_grp_temp["temp_bin"] = sensor_grp_temp["temp_bin"].astype(str)

    # get bin counts for each sensor-day combination
    sensor_grp_date = sensor_grp_temp.groupby(by=["zone", "temp_bin"])

    sensor_cnt = sensor_grp_date["temperature"].count().reset_index()
    sensor_cnt.rename(columns={"temperature": "temp_cnt"}, inplace=True)

    json_cnt = sensor_cnt.to_json(orient="records")
    # print(json_cnt)

    json_data = []

    json_temp = []

    for location_zone in location_zones:

        cnt_sensor = sensor_cnt[sensor_cnt["zone"] == location_zone]

        # del cnt_sensor["zone"]

        # Adding missing date/temp_bin combos
        bins_list, df_list, df_ = resample(cnt_sensor, TEMP_BINS, dt_from, dt_to)

        json_temp.append(df_.to_json(orient="records"))

        bins_json = []
        # df_temp.append(df_)

        for i, bin_range in enumerate(bins_list):
            temp_bin_df = df_list[i]
            # temp_bin_df["date"] = pd.to_datetime(
            #    temp_bin_df["date"], format="%Y-%m-%d"
            # ).dt.strftime("%Y-%m-%d")

            bins_json.append(
                '["' + bin_range + '",' + temp_bin_df.to_json(orient="records") + "]"
            )

        json_data.append("[" + ",".join(bins_json) + "]")

    sensor_temp_ranges["data"] = "[" + ",".join(json_data) + "]"

    return (
        location_zones,
        sensor_temp_ranges,
    )


@blueprint.route("/index")
@login_required
def index():
    """
    Index page
    """

    return render_template("index21.html")


test_json = [
    {
        "timestamp": "2021-07-07-21",
        "zone": "BackFarm",
        "date": 1625616000000,
        "sensor_id": 22.0,
        "temperature": 26.1875004768,
        "humidity": 73.0,
    },
    {
        "timestamp": "2021-07-07-21",
        "zone": "FrontFarm",
        "date": 1625616000000,
        "sensor_id": 21.0,
        "temperature": 20.2000007629,
        "humidity": 74.0,
    },
]


@blueprint.route("/<template>")
@login_required
def route_template(template):

    dt_to = dt.datetime.now()
    dt_from = dt_to - dt.timedelta(days=7)
    location_ids, sensor_temp_ranges, df_mean = zensie_query(dt_from, dt_to)
    df_ = temperature_analysis1(df_mean, dt_from, dt_to)

    data_to_frontend = (
        df_.groupby(["zone"], as_index=True)
        .apply(lambda x: x[["temp_bin", "temp_cnt"]].to_dict("r"))
        .reset_index()
        .rename(columns={0: "Values"})
        .to_json(orient="records")
    )

    print(data_to_frontend)

    a = "test!!"
    if template == "index21":
        return render_template(
            template + ".html",
            jim=location_ids,
            temperature_data=data_to_frontend,
            sum_zensie_locations=len(location_ids),
            zensie_locations=location_ids,
            zensie_temp_ranges=sensor_temp_ranges,
            dt_from=dt_from.strftime("%B %d, %Y"),
            dt_to=dt_to.strftime("%B %d, %Y"),
            # json_values=data_to_frontend,
        )
    if template == "index22":
        return render_template(
            template + ".html",
            temperature_data=data_to_frontend,
            dt_from=dt_from.strftime("%B %d, %Y"),
            dt_to=dt_to.strftime("%B %d, %Y"),
        )

    return render_template(template + ".html", jim=a)
