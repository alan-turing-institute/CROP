from app.home import blueprint
from flask import render_template, request
from flask_login import login_required
from sqlalchemy import and_

import copy

import datetime as dt

import numpy as np
import pandas as pd

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
    # print(df_list)

    return bins_list, df_list


# def weekly_calc (resampled_df_list):


def zensie_query(dt_from, dt_to, location_zone):
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
        # ReadingsZensieTRHClass.sensor_id,
        # SensorClass.name,
        ReadingsZensieTRHClass.temperature,
        ReadingsZensieTRHClass.humidity,
        SensorLocationClass.location_id,
        LocationClass.zone,
    ).filter(
        and_(
            # LocationClass.zone == location_zone,
            # SensorLocationClass.location_id == LocationClass.id,  # propagation location
            # ReadingsZensieTRHClass.sensor_id == SensorClass.id,
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
        location_zones, sensor_temp_ranges = temperature_range_analysis(
            df, dt_from, dt_to
        )

    else:
        location_zones = []
        sensor_temp_ranges = {}

    return location_zones, sensor_temp_ranges


# Temperature constants
TEMP_BINS = [0.0, 17.0, 21.0, 24.0, 30.0]


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

    df_unique_locations = df[["location_id"]].drop_duplicates(["location_id"])

    # location_ids = df_unique_locations["location_id"].tolist()
    location_zones = df_unique_locations["location_id"].tolist()

    # extracting date from datetime
    df["date"] = pd.to_datetime(df["timestamp"].dt.date)

    # Reseting index
    df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    # grouping data by location id
    sensor_grp = df.groupby(
        by=[
            df.timestamp.map(
                lambda x: "%04d-%02d-%02d-%02d" % (x.year, x.month, x.day, x.hour)
            ),
            "location_id",
            "date",
        ]
    )

    # estimating hourly temperature mean values
    sensor_grp_temp = sensor_grp["temperature"].mean().reset_index()
    # print(sensor_grp_temp)

    # for i in range(len(sensor_grp_temp)):
    #     if sensor_grp_temp["temperature"][i] > 24:
    #         print(sensor_grp_temp["temperature"][i])

    # binning temperature values
    sensor_grp_temp["temp_bin"] = pd.cut(sensor_grp_temp["temperature"], TEMP_BINS)

    # converting bins to str
    sensor_grp_temp["temp_bin"] = sensor_grp_temp["temp_bin"].astype(str)

    # get bin counts for each sensor-day combination
    sensor_grp_date = sensor_grp_temp.groupby(by=["location_id", "temp_bin"])

    sensor_cnt = sensor_grp_date["temperature"].count().reset_index()
    sensor_cnt.rename(columns={"temperature": "temp_cnt"}, inplace=True)

    json_data = []
    for location_zone in location_zones:

        cnt_sensor = sensor_cnt[sensor_cnt["location_id"] == location_zone]

        del cnt_sensor["location_id"]

        # Adding missing date/temp_bin combos
        bins_list, df_list = resample(cnt_sensor, TEMP_BINS, dt_from, dt_to)

        bins_json = []

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
    print(sensor_temp_ranges)
    return location_zones, sensor_temp_ranges


@blueprint.route("/<template>")
@login_required
def route_template(template):

    dt_to = dt.datetime.now()
    dt_from = dt_to - dt.timedelta(days=7)
    location_zones, sensor_temp_ranges = zensie_query(dt_from, dt_to, "Propagation")
    # print(sensor_temp_ranges)

    a = "test!!"
    if template == "index21":
        return render_template(
            template + ".html",
            jim=location_zones,
            sum_zensie_locations=len(location_zones),
            zensie_locations=location_zones,
            zensie_temp_ranges=sensor_temp_ranges,
            dt_from=dt_from.strftime("%B %d, %Y"),
            dt_to=dt_to.strftime("%B %d, %Y"),
        )

    return render_template(template + ".html", jim=a)
