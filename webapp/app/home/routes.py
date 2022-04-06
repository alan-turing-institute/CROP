"""
A module for the main dashboard actions
"""
import logging
import copy
import datetime as dt
import pandas as pd

from flask import render_template, request
from flask_login import login_required
from sqlalchemy import and_

from app.home import blueprint

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass,
    LocationClass,
    SensorLocationClass,
    ReadingsZensieTRHClass,
)
from __app__.crop.constants import CONST_TIMESTAMP_FORMAT

TEMP_BINS = {
    "Propagation": [0.0, 20.0, 23.0, 25.0, 144.0],  # optimal 23
    "FrontFarm": [0.0, 18.0, 21.0, 25.0, 144.0],  # optimal 21
    "Fridge": [0.0, 20.0, 23.0, 25.0, 144.0],  # optimal 23
    "MidFarm": [0.0, 20.0, 23.0, 25.0, 144.0],  # optimal 23
    "BackFarm": [0.0, 20.0, 25.0, 28.0, 144.0],  # optimal 25
    "R&D": [0.0, 20.0, 23.0, 25.0, 144.0],  # optimal 23
}
HUM_BINS = {
    "Propagation": [0.0, 50.0, 65.0, 85.0, 100.0],  # optimal 70
    "FrontFarm": [0.0, 50.0, 65.0, 85.0, 100.0],  # optimal 70
    "Fridge": [0.0, 50.0, 65.0, 85.0, 100.0],  # optimal 70
    "MidFarm": [0.0, 50.0, 65.0, 85.0, 100.0],  # optimal 70
    "BackFarm": [0.0, 50.0, 65.0, 85.0, 100.0],  # optimal 70,
    "R&D": [0.0, 50.0, 65.0, 85.0, 100.0],  # optimal 70,
}
LOCATION_ZONES = ["Propagation", "FrontFarm", "MidFarm", "BackFarm", "R&D"]


def resample(df_, bins):
    """
    Resamples (adds missing date/temperature bin combinations) to a dataframe.

    Arguments:
        temp_df: dataframe with temperature assign to bins
        bins: temperature or humidity bins as a list
    Returns:
        temp_df: the df with grouped bins
    """

    bins_list = [
        "(%.1f, %.1f]" % (bins[i], bins[i + 1]) for i in range(len(bins) - 1)
    ]

    # resamples with 0 if there are no data in a bin
    for temp_range in bins_list:
        if len(df_[(df_["bin"] == temp_range)].index) == 0:

            df2 = pd.DataFrame({"bin": [temp_range], "cnt": [0]})

            df_ = df_.append(df2)

    df_out = df_.sort_values(by=["bin"], ascending=True)

    df_out.reset_index(inplace=True, drop=True)

    return df_out


# def warnings_query(dt_from, dt_to):
#     """
#     Performs a query for warnings.

#     Arguments:
#         dt_from_: date range from
#         dt_to_: date range to
#     Returns:
#         df: a df with the queried data
#     """
#     query = db.session.query(

#         LocationClass.zone,
#     ).filter(
#         and_(
#             SensorLocationClass.location_id == LocationClass.id,
#             ReadingsZensieTRHClass.sensor_id == SensorClass.id,
#             ReadingsZensieTRHClass.sensor_id == SensorLocationClass.sensor_id,
#             ReadingsZensieTRHClass.timestamp >= dt_from,
#             ReadingsZensieTRHClass.timestamp <= dt_to,
#         )
#     )

#     df = pd.read_sql(query.statement, query.session.bind)

#     logging.info("Total number of records found: %d" % (len(df.index)))
#     if df.empty:
#         logging.debug("WARNING: Query returned empty")

#     return df


def zensie_query(dt_from, dt_to):
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

    if df.empty:
        logging.debug("WARNING: Query returned empty")

    return df


def grp_per_hr_zone(temp_df):
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

    # df["timestamp"] = pd.to_datetime(df["timestamp"])

    # mask per selected date
    # mask = (df["timestamp"] >= dt_from) & (df["timestamp"] <= dt_to)
    # filtered_df = df.loc[mask]

    # extracting date from datetime
    df["date"] = pd.to_datetime(df["timestamp"].dt.date)

    # Reseting index
    df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    df_grp_zone_hr = (
        df.groupby(
            by=[
                df.timestamp.map(
                    lambda x: "%04d-%02d-%02d-%02d"
                    % (x.year, x.month, x.day, x.hour)
                ),
                "zone",
                "date",
            ]
        )
        .mean()
        .reset_index()
    )

    return df_grp_zone_hr


def stratification(temp_df, sensor_ids):
    """
    Extract the Zensie data from `temp_df` for different sensors, write as
    JSON. Used for comparing e.g. front vs back or top vs bottom of the farm.

    Arguments:
        temp_df: Zensie data as a DataFrame
        sensor_ids: Iterable of sensor IDs for each to include data
    Returns:
        json_strat: A json string containing hourly values for the time series
            plot in front end for selected sensors.
    """
    df = copy.deepcopy(temp_df)

    # extracting date from datetime
    df["date"] = pd.to_datetime(df["timestamp"].dt.date)

    # Reseting index
    df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

    df_ = df.loc[df["sensor_id"].isin(sensor_ids)]
    df_grp_hr = (
        df_.groupby(
            by=[
                df_.timestamp.map(
                    lambda x: "%04d-%02d-%02dT%02d"
                    % (x.year, x.month, x.day, x.hour)
                ),
                "date",
                "sensor_id",
            ]
        )
        .mean()
        .reset_index()
    )

    json_strat = (
        df_grp_hr.groupby(["sensor_id"], as_index=True)
        .apply(
            lambda x: x[["temperature", "humidity", "timestamp"]].to_dict(
                orient="records"
            )
        )
        .to_json(orient="index")
    )

    return json_strat


def bin_zensie_data(df, bins, zensie_measure, expected_total=None):
    """
    Return a dataframe with counts of how many measurements of zensie_measure
    were in each of the bins, by zone.
    Arguments:
        df: data
        bins: a list of bins to perform the analysis
        zensie_measure: Either "temperature" or "humidity".

    Returns:
        output: A merged df with counts per bin
    """
    output_list = []
    for zone in LOCATION_ZONES:
        # check if zone exists in current bins dictionary:
        if zone not in bins:
            logging.info(
                "WARNING: %s doesn't exist in current bin dictionary" % zone
            )
            continue

        df_each_zone = df.loc[df.zone == zone, :].copy()
        # breaks df in
        df_each_zone["bin"] = pd.cut(df_each_zone[zensie_measure], bins[zone])
        # converting bins to str
        df_each_zone["bin"] = df_each_zone["bin"].astype(str)
        # groups df per each bin
        bin_grp = df_each_zone.groupby(by=["zone", "bin"])
        # get measure counts per bin
        bin_cnt = bin_grp[zensie_measure].count().reset_index()
        # renames column with counts
        bin_cnt.rename(columns={zensie_measure: "cnt"}, inplace=True)
        df_ = resample(bin_cnt, bins[zone])
        if expected_total:
            total = df_["cnt"].sum()
            df_.loc[df.index.max() + 1] = [
                zone,
                "missing",
                expected_total - total,
            ]
        # renames the values of all the zones
        df_["zone"] = zone
        output_list.append(df_)

    # Merge all df in one.
    output = pd.concat(output_list, ignore_index=True)
    return output


def json_bin_counts(df):
    """
    Function to return the Json for the bin count pie charts in the main
    dashboard.
    """
    output = (
        df.groupby(["zone"], as_index=True)
        .apply(lambda x: x[["bin", "cnt"]].to_dict(orient="records"))
        .reset_index()
        .rename(columns={0: "Values"})
        .to_json(orient="records")
    )
    return output


def json_hum(df_hum):
    """
    Function to return the Json for the humidity related
    charts in the main dashboard

    """
    return (
        df_hum.groupby(["zone"], as_index=True)
        .apply(lambda x: x[["bin", "cnt"]].to_dict("r"))
        .reset_index()
        .rename(columns={0: "Values"})
        .to_json(orient="records")
    )


def current_values_json(df_hourly):

    df_test = df_hourly.loc[df_hourly.groupby("zone").timestamp.idxmax()]
    df_test["temperature"] = df_test["temperature"].astype(int)

    for i in range(len(LOCATION_ZONES)):

        if not df_test["zone"].str.contains(LOCATION_ZONES[i]).any():
            df2 = pd.DataFrame({"zone": [LOCATION_ZONES[i]]})
            df_test = df_test.append(df2)

    return df_test.to_json(orient="records")


# @blueprint.route("/<template>")
# @login_required
# def route_template(template):


@blueprint.route("/index")
@login_required
def index():
    """
    Index page
    """
    dt_to = dt.datetime.now()
    dt_from_weekly = dt_to - dt.timedelta(days=7)
    dt_from_daily = dt_to - dt.timedelta(days=1)
    dt_from_hourly = dt_to - dt.timedelta(hours=2)

    # weekly
    df = zensie_query(dt_from_weekly, dt_to)
    if not df.empty:
        df_mean_hr_weekly = grp_per_hr_zone(df)
        df_temp_weekly = bin_zensie_data(
            df_mean_hr_weekly, TEMP_BINS, "temperature", expected_total=24 * 7
        )
        df_hum_weekly = bin_zensie_data(
            df_mean_hr_weekly, HUM_BINS, "humidity", expected_total=24 * 7
        )
        weekly_temp_json = json_bin_counts(df_temp_weekly)
        weekly_hum_json = json_bin_counts(df_hum_weekly)
        # Sensor id locations:
        # 18: 16B1, 21: 1B2, 22: 29B2, 23: 16B4
        json_strat = stratification(df, (18, 21, 22, 23))
    else:
        weekly_temp_json = {}
        weekly_hum_json = {}
        json_vertstrat = {}

    df_daily = zensie_query(dt_from_daily, dt_to)
    if not df_daily.empty:
        df_mean_hr_daily = grp_per_hr_zone(df_daily)
        df_temp_daily = bin_zensie_data(
            df_mean_hr_daily, TEMP_BINS, "temperature", expected_total=24
        )
        df_hum_daily = bin_zensie_data(
            df_mean_hr_daily, HUM_BINS, "humidity", expected_total=24
        )
        daily_temp_json = json_bin_counts(df_temp_daily)
        daily_hum_json = json_bin_counts(df_hum_daily)
    else:
        daily_temp_json = {}
        daily_hum_json = {}

    df_hourly = zensie_query(dt_from_hourly, dt_to)
    if not df_hourly.empty:
        hourly_json = current_values_json(df_hourly)
    else:
        hourly_json = {}

    return render_template(
        "index.html",
        hourly_data=hourly_json,
        temperature_data=weekly_temp_json,
        humidity_data=weekly_hum_json,
        temperature_data_daily=daily_temp_json,
        humidity_data_daily=daily_hum_json,
        stratification=json_strat,
        dt_from=dt_from_weekly.strftime("%B %d, %Y"),
        dt_to=dt_to.strftime("%B %d, %Y"),
    )


@blueprint.route("/model")
@login_required
def model():
    """Unity model page."""
    return render_template("model.html",)
