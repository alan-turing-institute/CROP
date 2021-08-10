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
from __app__.crop.constants import CONST_TIMESTAMP_FORMAT

TEMP_BINS = {
    "Propagation": [0.0, 20.0, 23.0, 25.0, 35.0],  # optimal 23
    "FrontFarm": [0.0, 18.0, 21.0, 25.0, 35.0],  # optimal 21
    "Fridge": [0.0, 20.0, 23.0, 25.0, 35.0],  # optimal 23
    "MidFarm": [0.0, 20.0, 23.0, 25.0, 35.0],  # optimal 23
    "BackFarm": [0.0, 20.0, 25.0, 28.0, 35.0],  # optimal 25
    "R&D": [0.0, 20.0, 23.0, 25.0, 35.0],  # optimal 23
}
HUM_BINS = {
    "Propagation": [0.0, 50.0, 65.0, 75.0, 85.0],  # optimal 70
    "FrontFarm": [0.0, 50.0, 65.0, 75.0, 85.0],  # optimal 70
    "Fridge": [0.0, 50.0, 65.0, 75.0, 85.0],  # optimal 70
    "MidFarm": [0.0, 50.0, 65.0, 75.0, 85.0],  # optimal 70
    "BackFarm": [0.0, 50.0, 65.0, 75.0, 85.0],  # optimal 70,
    "R&D": [0.0, 50.0, 65.0, 75.0, 85.0],  # optimal 70,
}


def resample(df, bins):
    """
    Resamples (adds missing date/temperature bin combinations) to a dataframe.

    Arguments:
        df: dataframe with temperature assign to bins
        bins: temperature or humidity bins as a list
    Returns:
        df: the df with grouped bins
    """

    bins_list = []
    for i in range(len(bins) - 1):
        bins_list.append("(%.1f, %.1f]" % (bins[i], bins[i + 1]))

    for temp_range in bins_list:
        if len(df[(df["bin"] == temp_range)].index) == 0:

            df2 = pd.DataFrame({"bin": [temp_range], "cnt": [0]})

            df = df.append(df2)

    df = df.sort_values(by=["bin"], ascending=True)

    df.reset_index(inplace=True, drop=True)

    return df




def zensie_query(
    dt_from,
    dt_to,
):
    """
    Performs a query for zensie sensors.

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
    Returns:
        df: a df with the queried data
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
        return df

    else:
        df = df.empty

    return df


def grp_per_hr_zone(temp_df, dt_from, dt_to):
    """
    finds mean of values per hour for a selected date.
    Returns a dataframe ready for json

    Arguments:
        temp_df:
        dt_from: date range from
        dt_to: date range to
    Returns:
        df_grp_zone_hr: df with temperate ranges
    """

    df = copy.deepcopy(temp_df)

    # mask per selected date
    mask = (df["timestamp"] >= dt_from) & (df["timestamp"] <= dt_to)
    filtered_df = df.loc[mask]

    # extracting date from datetime
    filtered_df["date"] = pd.to_datetime(filtered_df["timestamp"].dt.date)

    # Reseting index
    filtered_df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    df_grp_zone_hr = (
        filtered_df.groupby(
            by=[
                filtered_df.timestamp.map(
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


def vertical_stratification(temp_df, dt_from, dt_to, bot_sensor_id, top_sensor_id):
    """
    Function to do the vertical stratification for the middle of the farm
    sensors: 16B1 and 16B4, and returned Json. 
    Arguments:
        temp_df: data
        dt_from: date range from
        dt_to: date range to
        bot_sensor_id: sensor Id installed at the bottom of the farm 
        top_sensor_id: sensor id installed at the top part of the farm
    Returns:
        json_VS: A json file containing (bot and top) hourly values for the 
        time series plot in front end 
    """
    df = copy.deepcopy(temp_df)

    # mask per selected date
    mask = (df["timestamp"] >= dt_from) & (df["timestamp"] <= dt_to)
    filtered_df = df.loc[mask]

    # extracting date from datetime
    filtered_df["date"] = pd.to_datetime(filtered_df["timestamp"].dt.date)

    # Reseting index
    filtered_df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    df_ = filtered_df.loc[
        (df["sensor_id"] == bot_sensor_id) | (df["sensor_id"] == top_sensor_id)
    ]

    df_grp_hr = (
        df_.groupby(
            by=[
                df_.timestamp.map(
                    lambda x: "%04d-%02d-%02d-%02d" % (x.year, x.month, x.day, x.hour)
                ),
                "date",
                "sensor_id",
            ]
        )
        .mean()
        .reset_index()
    )

    json_VS = (
        df_grp_hr.groupby(["sensor_id"], as_index=True)
        .apply(lambda x: x[["temperature", "humidity", "date"]].to_dict("r"))
        .reset_index()
        .rename(columns={0: "Values"})
        .to_json(orient="records")
    )

    return json_VS


def temperature_analysis(df, dt_from, dt_to, bins):
    """
    Function to perform temerature analysis per location of the farm.
    Counts the number of instances that occur per temp. bin. 
    Arguments:
        df: data
        dt_from: date range from
        dt_to: date range to
        bins: a list of bins to perform the analysis

    Returns:
        temp_df_merged: A merged df with sampled values per bin
     """
    df_unique_zones = df[["zone"]].drop_duplicates(["zone"])
    location_zones = df_unique_zones["zone"].tolist()
    # sensor_grp_temp = zone_hr_grp["temperature"].mean().reset_index()

    temp_list = []

    for zone in location_zones:

        #check if zone exists in current bins dictionary:
        if (zone in bins):

            df_each_zone = df[df.zone == zone]
            
            # breaks df in temperature bins
            df_each_zone["bin"] = pd.cut(df_each_zone["temperature"], bins[zone])

            # converting bins to str
            df_each_zone["bin"] = df_each_zone["bin"].astype(str)

            # groups df per each bin
            bin_grp = df_each_zone.groupby(by=["zone", "bin"])

            # get temperature counts per bin
            bin_cnt = bin_grp["temperature"].count().reset_index()

            # renames column with counts
            bin_cnt.rename(columns={"temperature": "cnt"}, inplace=True)

            df_ = resample(bin_cnt, bins[zone])

            # renames the values of all the zones
            df_["zone"] = zone

            # fixes the labels of the bins by removing uncessesary characters((0.0, 25.0]) )
            for j in range(len(df_["bin"])):
                fixed_label = (
                    df_["bin"][j]
                    .replace("(", "")
                    .replace("]", "")
                    .replace(", ", "-")
                    .replace(".0", "")
                )
                df_["bin"][j] = fixed_label

            temp_list.append(df_)
            
        else: logging.info("WARNING: %s doesn't exist in current temp bin dictionary" % zone) 

    # merges all df in one.
    temp_df_merged = pd.concat(temp_list)

    return temp_df_merged


def humidity_analysis(df, dt_from, dt_to, bins):
    """
    Function to perform humidity analysis per location of the farm.
    Counts the number of instances that occur per temp. bin. 
    Arguments:
        df: data
        dt_from: date range from
        dt_to: date range to
        bins: a list of bins to perform the analysis

    Returns:
        temp_df_merged: A merged df with sampled values per bin
 
    """
    df_unique_zones = df[["zone"]].drop_duplicates(["zone"])
    location_zones = df_unique_zones["zone"].tolist()

    hum_list = []
    for zone in location_zones:
        if (zone in bins):

            df_each_zone = df[df.zone == zone]

            # breaks df in temperature bins
            df_each_zone["bin"] = pd.cut(df_each_zone["humidity"], bins[zone])

            # converting bins to str
            df_each_zone["bin"] = df_each_zone["bin"].astype(str)

            # groups df per each bin
            bin_grp = df_each_zone.groupby(by=["zone", "bin"])

            # get temperature counts per bin
            bin_cnt = bin_grp["humidity"].count().reset_index()

            # renames column with counts
            bin_cnt.rename(columns={"humidity": "cnt"}, inplace=True)

            df_ = resample(bin_cnt, bins[zone])

            # renames the values of all the zones
            df_["zone"] = zone

            # formats the labels of the bins by removing uncessesary characters((0.0, 25.0]) )
            for j in range(len(df_["bin"])):
                fixed_label = (
                    df_["bin"][j]
                    .replace("(", "")
                    .replace("]", "")
                    .replace(", ", "-")
                    .replace(".0", "")
                )
                df_["bin"][j] = fixed_label

            hum_list.append(df_)
        else: logging.info("WARNING: %s doesn't exist in current hum bin dictionary" % zone) 

    # merges all df in one.
    hum_df_merged = pd.concat(hum_list) 

    return hum_df_merged


def Prepare_Json_temp(df):
    """
    Function to return the Json for the temperature related 
    charts in the main dashboard
 
    """
    return (
        df.groupby(["zone"], as_index=True)
        .apply(lambda x: x[["bin", "cnt"]].to_dict("r"))
        .reset_index()
        .rename(columns={0: "Values"})
        .to_json(orient="records")
    )


def Prepare_Json_hum(df):
    """
    Function to return the Json for the humidity related 
    charts in the main dashboard
 
    """
    return (
        df.groupby(["zone"], as_index=True)
        .apply(lambda x: x[["bin", "cnt"]].to_dict("r"))
        .reset_index()
        .rename(columns={0: "Values"})
        .to_json(orient="records")
    )

@blueprint.route("/index")
@login_required
def index():
    """
    Index page
    """

    return render_template("index22.html")


@blueprint.route("/<template>")
@login_required
def route_template(template):

    dt_to = dt.datetime.now()
    dt_from = dt_to - dt.timedelta(days=7)
    dt_from_daily = dt_to - dt.timedelta(days=1)

    df = zensie_query(dt_from, dt_to)

    df_mean_hr_weekly = grp_per_hr_zone(df, dt_from, dt_to)
    df_mean_hr_daily = grp_per_hr_zone(df, dt_from_daily, dt_to)

    df_temp_weekly = temperature_analysis(df_mean_hr_weekly, dt_from, dt_to, TEMP_BINS)
    df_hum_weekly = humidity_analysis(df_mean_hr_weekly, dt_from, dt_to, HUM_BINS)
    df_temp_daily = temperature_analysis(
        df_mean_hr_daily, dt_from_daily, dt_to, TEMP_BINS
    )
    df_hum_daily = humidity_analysis(df_mean_hr_daily, dt_from_daily, dt_to, HUM_BINS)

    weekly_temp_json = Prepare_Json_temp(df_temp_weekly)
    weekly_hum_json = Prepare_Json_temp(df_hum_weekly)
    daily_temp_json = Prepare_Json_temp(df_temp_daily)
    daily_hum_json = Prepare_Json_temp(df_hum_daily)

    # data_to_frontend = weekly_temp_json # for the end merged json
    #VS_json = vertical_stratification(
    #    df, 23, 18, dt_from, dt_to
    #)  # sensorids in positions (16B1 and 16B4)
    # print(data_to_frontend)

    if template == "index22":
        return render_template(
            template + ".html",
            temperature_data=weekly_temp_json,
            humidity_data=weekly_hum_json,
            temperature_data_daily=daily_temp_json,
            humidity_data_daily=daily_hum_json,
            #vertical_stratification=VS_json,
            dt_from=dt_from.strftime("%B %d, %Y"),
            dt_to=dt_to.strftime("%B %d, %Y"),
        )

    return render_template(template + ".html")
