from app.home import blueprint

import copy
from datetime import timedelta

import numpy as np
import pandas as pd

import logging

from flask_login import login_required
from flask import render_template, request
from sqlalchemy import and_

from app.dashboards import blueprint

from utilities.utils import parse_date_range_argument

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass,
    LocationClass,
    SensorLocationClass,
    ReadingsZensieTRHClass,
)
from __app__.crop.constants import CONST_MAX_RECORDS, CONST_TIMESTAMP_FORMAT


@blueprint.route("/<template>")
@login_required
def route_template(template):

    return render_template(template + ".html")


def db_query_tmpr_day_zenzie(session, location_zone, date_range):

    """
    Function to query temperature readings from the Crop dabase's
    zenzie sensors located in the propagation area of the farm
    location_zone (str): the zone of the farm to query
    """

    query = session.query(
        ReadingsZensieTRHClass.temperature,
        ReadingsZensieTRHClass.humidity,
        # ReadingsZensieTRHClass.sensor_id,
    ).filter(
        and_(
            LocationClass.zone == location_zone,
            SensorLocationClass.location_id == LocationClass.id,  # propagation location
            # SensorLocationClass.location_id == location_id,
            ReadingsZensieTRHClass.sensor_id == SensorLocationClass.sensor_id,
            ReadingsZensieTRHClass.time_created >= date_range,
        )
    )
    readings = session.execute(query).fetchall()
    # TODO: r = query_result_to_array(readings)

    return readings


def zensie_analysis(dt_from, dt_to, location_zone):
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
            LocationClass.zone == location_zone,
            SensorLocationClass.location_id == LocationClass.id,  # propagation location
            ReadingsZensieTRHClass.timestamp >= dt_from,
            ReadingsZensieTRHClass.timestamp <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    logging.info("Total number of records found: %d" % (len(df.index)))

    if not df.empty:
        sensor_names, sensor_temp_ranges = temperature_range_analysis(
            df, dt_from, dt_to
        )

    else:
        sensor_names = []
        sensor_temp_ranges = {}

    return sensor_names, sensor_temp_ranges


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

    df_unique_sensors = df[["sensor_id", "name"]].drop_duplicates(["sensor_id", "name"])

    sensor_ids = df_unique_sensors["sensor_id"].tolist()
    sensor_names = df_unique_sensors["name"].tolist()

    # extracting date from datetime
    df["date"] = pd.to_datetime(df["timestamp"].dt.date)

    # Reseting index
    df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    # grouping data by date-hour and sensor id
    sensor_grp = df.groupby(
        by=[
            df.timestamp.map(
                lambda x: "%04d-%02d-%02d-%02d" % (x.year, x.month, x.day, x.hour)
            ),
            "sensor_id",
            "date",
        ]
    )

    # estimating hourly temperature mean values
    sensor_grp_temp = sensor_grp["temperature"].mean().reset_index()

    # binning temperature values
    sensor_grp_temp["temp_bin"] = pd.cut(sensor_grp_temp["temperature"], TEMP_BINS)

    # converting bins to str
    sensor_grp_temp["temp_bin"] = sensor_grp_temp["temp_bin"].astype(str)

    # get bin counts for each sensor-day combination
    sensor_grp_date = sensor_grp_temp.groupby(by=["sensor_id", "date", "temp_bin"])

    sensor_cnt = sensor_grp_date["temperature"].count().reset_index()
    sensor_cnt.rename(columns={"temperature": "temp_cnt"}, inplace=True)

    json_data = []
    for sensor_id in sensor_ids:

        cnt_sensor = sensor_cnt[sensor_cnt["sensor_id"] == sensor_id]

        del cnt_sensor["sensor_id"]

        # Adding missing date/temp_bin combos
        bins_list, df_list = resample(cnt_sensor, TEMP_BINS, dt_from, dt_to)

        bins_json = []

        for i, bin_range in enumerate(bins_list):
            temp_bin_df = df_list[i]
            temp_bin_df["date"] = pd.to_datetime(
                temp_bin_df["date"], format="%Y-%m-%d"
            ).dt.strftime("%Y-%m-%d")

            bins_json.append(
                '["' + bin_range + '",' + temp_bin_df.to_json(orient="records") + "]"
            )

        json_data.append("[" + ",".join(bins_json) + "]")

    sensor_temp_ranges["data"] = "[" + ",".join(json_data) + "]"

    return sensor_names, sensor_temp_ranges
