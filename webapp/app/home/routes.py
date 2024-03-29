"""
A module for the main dashboard actions
"""
import logging
import copy
import datetime as dt
import numpy as np
import pandas as pd
import json
import pytz

from flask import render_template, request
from flask_login import login_required
from sqlalchemy import and_

from app.home import blueprint

from cropcore.constants import CONST_TIMESTAMP_FORMAT
from cropcore import queries
from cropcore.structure import SQLA as db
from cropcore.structure import (
    LocationClass,
    ReadingsAranetTRHClass,
    SensorClass,
    SensorLocationClass,
    TypeClass,
    WarningClass,
    WarningTypeClass,
)

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
VPD_BINS = {
    "Propagation": [0.0, 300.0, 600.0, 1000.0, 10000.0],
    "FrontFarm": [0.0, 300.0, 600.0, 1000.0, 10000.0],
    "Fridge": [0.0, 300.0, 600.0, 1000.0, 10000.0],
    "MidFarm": [0.0, 300.0, 600.0, 1000.0, 10000.0],
    "BackFarm": [0.0, 300.0, 600.0, 1000.0, 10000.0],
    "R&D": [0.0, 300.0, 600.0, 1000.0, 10000.0],
}
LOCATION_REGIONS = ["Propagation", "FrontFarm", "MidFarm", "BackFarm", "R&D"]


def resample(df_, bins):
    """
    Resamples (adds missing date/temperature bin combinations) to a dataframe.

    Arguments:
        temp_df: dataframe with temperature assign to bins
        bins: temperature or humidity bins as a list
    Returns:
        temp_df: the df with grouped bins
    """

    bins_list = ["(%.1f, %.1f]" % (bins[i], bins[i + 1]) for i in range(len(bins) - 1)]

    # resamples with 0 if there are no data in a bin
    for temp_range in bins_list:
        if len(df_[(df_["bin"] == temp_range)].index) == 0:
            df2 = pd.DataFrame({"bin": [temp_range], "cnt": [0]})
            df_ = pd.concat([df_, df2])

    df_out = df_.sort_values(by=["bin"], ascending=True)
    df_out.reset_index(inplace=True, drop=True)
    return df_out


def aranet_query(dt_from, dt_to):
    """
    Performs a query for Aranet T/RH sensors.

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
    Returns:
        df: a df with the queried data
    """

    logging.info(
        "Getting Aranet readings dataframe with parameters %s %s"
        % (
            dt_from.strftime(CONST_TIMESTAMP_FORMAT),
            dt_to.strftime(CONST_TIMESTAMP_FORMAT),
        )
    )

    trh_query = queries.trh_with_vpd(db.session).subquery()
    latest_locations_query = queries.latest_sensor_locations(db.session).subquery()
    locations_query = queries.locations_with_extras(db.session).subquery()

    query = db.session.query(
        trh_query.c.temperature,
        trh_query.c.humidity,
        trh_query.c.vpd,
        trh_query.c.timestamp,
        trh_query.c.sensor_id,
        locations_query.c.region,
    ).filter(
        and_(
            trh_query.c.timestamp >= dt_from,
            trh_query.c.timestamp <= dt_to,
            trh_query.c.sensor_id == latest_locations_query.c.sensor_id,
            latest_locations_query.c.location_id == locations_query.c.id,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)
    df["timestamp"] = df["timestamp"].dt.tz_localize(dt.timezone.utc)

    logging.info("Total number of records found: %d" % (len(df.index)))
    if df.empty:
        logging.debug("WARNING: Query returned empty")
    return df


def grp_per_hr_region(df):
    """
    Compute hourly means of the T&RH dataframe.
    """
    df = copy.deepcopy(df)
    # extracting date from datetime
    if len(df) > 0:
        df["date"] = pd.to_datetime(df["timestamp"].dt.date)
    else:
        df["date"] = []
    # Reseting index
    df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)
    if len(df) > 0:
        df_grp_region_hr = (
            df.groupby(
                by=[
                    df.timestamp.map(
                        lambda x: "%04d-%02d-%02d-%02d"
                        % (x.year, x.month, x.day, x.hour)
                    ),
                    "region",
                    "date",
                ]
            )
            .mean()
            .reset_index()
        )
    else:
        df_grp_region_hr = df
    return df_grp_region_hr


def stratification(temp_df, sensor_ids):
    """
    Extract the T&RH data from `temp_df` for different sensors, write as JSON. Used for
    comparing e.g. front vs back or top vs bottom of the farm.

    Arguments:
        temp_df: T&RH data as a DataFrame
        sensor_ids: Iterable of sensor IDs for each to include data
    Returns:
        json_strat: A json string containing hourly values for the time series
            plot in front end for selected sensors.
    """
    df = copy.deepcopy(temp_df)

    # extracting date from datetime
    df["date"] = pd.to_datetime(df["timestamp"].dt.date)

    # Reseting index
    df = df.sort_values(by=["timestamp"], ascending=True).reset_index()

    df_ = df.loc[df["sensor_id"].isin(sensor_ids)]
    json_strat = (
        df_.groupby(["sensor_id"], as_index=True)
        .apply(
            lambda x: x[["temperature", "humidity", "vpd", "timestamp"]].to_dict(
                orient="records"
            )
        )
        .to_json(orient="index")
    )

    return json_strat


def bin_trh_data(df, bins, measure, expected_total=None):
    """
    Return a dataframe with counts of how many measurements of `measure` were in each of
    the bins, by region.

    Arguments:
        df: data
        bins: a list of bins to perform the analysis
        measure: Either "temperature" or "humidity".
        expected_total: Total number of entries we expect. Optional. If provided,
            "missing" will be added for as many entries as we are short of the expected.

    Returns:
        output: A merged df with counts per bin
    """
    output_list = []
    for region in LOCATION_REGIONS:
        # check if region exists in current bins dictionary:
        if region not in bins:
            logging.info("WARNING: %s doesn't exist in current bin dictionary" % region)
            continue

        df_each_region = df.loc[df.region == region, :].copy()
        # breaks df in
        df_each_region["bin"] = pd.cut(df_each_region[measure], bins[region])
        # converting bins to str
        df_each_region["bin"] = df_each_region["bin"].astype(str)
        # groups df per each bin
        bin_grp = df_each_region.groupby(by=["region", "bin"])
        # get measure counts per bin
        bin_cnt = bin_grp[measure].count().reset_index()
        # renames column with counts
        bin_cnt.rename(columns={measure: "cnt"}, inplace=True)
        df_ = resample(bin_cnt, bins[region])
        if expected_total:
            total = df_["cnt"].sum()
            df_.loc[df.index.max() + 1] = [region, "missing", expected_total - total]
        # renames the values of all the regions
        df_["region"] = region
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
        df.groupby(["region"], as_index=True)
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
        df_hum.groupby(["region"], as_index=True)
        .apply(lambda x: x[["bin", "cnt"]].to_dict("r"))
        .reset_index()
        .rename(columns={0: "Values"})
        .to_json(orient="records")
    )


def regional_mean_json(df_hourly):
    """Compute a DataFrame with the per-region means of the inputs T&RH columns."""
    latest_readings_by_sensor = df_hourly.groupby("sensor_id")["timestamp"].idxmax()
    df_mean = df_hourly.loc[latest_readings_by_sensor, :]
    df_mean = (
        df_mean.loc[
            :,
            ["temperature", "humidity", "vpd", "timestamp", "region"],
        ]
        .groupby("region")
        .mean()
    ).reset_index()

    # Add empty rows for regions that are missing.
    for i in range(len(LOCATION_REGIONS)):
        if not df_mean["region"].str.contains(LOCATION_REGIONS[i]).any():
            df2 = pd.DataFrame({"region": [LOCATION_REGIONS[i]]})
            df_mean = pd.concat([df_mean, df2])

    return_value = df_mean.to_json(orient="records")
    return return_value


def regional_minmax_json(df):
    """Compute a DataFrame with the per-region min/max of the inputs T&RH columns."""
    df_minmax = (
        df.loc[:, ["temperature", "humidity", "vpd", "region"]]
        .groupby("region")
        .agg(["min", "max"])
    ).reset_index()

    # Add empty rows for regions that are missing.
    for i in range(len(LOCATION_REGIONS)):
        if not df_minmax["region"].str.contains(LOCATION_REGIONS[i]).any():
            new_row = {
                column: [np.nan]
                for column in df_minmax.columns
                if column != ("region", "")
            }
            new_row[("region", "")] = [LOCATION_REGIONS[i]]
            df2 = pd.DataFrame(
                data=new_row, columns=pd.MultiIndex.from_tuples(df_minmax.columns)
            )
            df_minmax = pd.concat([df_minmax, df2], ignore_index=True)

    df_minmax = pd.melt(df_minmax, id_vars=["region"])
    df_minmax["timestamp"] = df_minmax.apply(
        lambda row: df.loc[
            (df["region"] == row["region"]) & (df[row["variable_0"]] == row["value"]),
            "timestamp",
        ].max(),
        axis=1,
    )

    return_value = df_minmax.to_json(orient="records")
    return return_value


def get_warning_categories():
    """Get the all the warning categories from the CROP database.

    Return
    a) a list of dictionaries, one for each category, with keys "name" and "id".
    The ids are integers we generate in this function, the names are the category values
    in the database.
    b) Dictionary mapping warning_type IDs to category IDs.
    """
    query = db.session.query(
        WarningTypeClass.id, WarningTypeClass.name, WarningTypeClass.category
    )
    warning_types = pd.read_sql(query.statement, query.session.bind)
    category_names = warning_types["category"].unique()
    categories = [
        {"cat_id": index, "cat_name": cat_name}
        for index, cat_name in enumerate(category_names)
    ]
    cat_ids_by_name = {cat["cat_name"]: cat["cat_id"] for cat in categories}
    categories_by_type = {
        warning_type["id"]: cat_ids_by_name[warning_type["category"]]
        for _, warning_type in warning_types.iterrows()
    }
    return categories, categories_by_type


def get_warnings(time_from):
    """Get the latest alerts from the CROP database as a pandas DataFrame."""
    query = (
        db.session.query(
            WarningClass.sensor_id,
            WarningClass.batch_id,
            WarningClass.time,
            WarningClass.other_data,
            WarningClass.priority,
            WarningClass.time_created,
            WarningTypeClass.id.label("type_id"),
            WarningTypeClass.name.label("type_name"),
            WarningTypeClass.short_description,
            WarningTypeClass.long_description,
            SensorClass.name.label("sensor_name"),
        )
        .outerjoin(
            SensorClass,
            SensorClass.id == WarningClass.sensor_id,
        )
        .filter(
            and_(
                WarningTypeClass.id == WarningClass.warning_type_id,
                WarningClass.time_created > time_from,
            )
        )
    )
    warnings = pd.read_sql(query.statement, query.session.bind)
    if len(warnings) > 0:
        warnings["time_created"] = warnings["time_created"].dt.tz_localize(
            dt.timezone.utc
        )
        warnings["description"] = warnings.apply(
            lambda row: row["short_description"].format(
                sensor_id=row["sensor_id"],
                sensor_name=row["sensor_name"],
                batch_id=row["batch_id"],
                time=row["time"],
                **({} if row["other_data"] is None else row["other_data"]),
            ),
            axis=1,
        )
    else:
        warnings["description"] = []
    # Drop all the columns we don't need, and pick the latest version of each warning
    # only.
    # Why include sensor_id, batch_id, and other_data in this groupby, since
    # they've already done their job in filling in the fields for description? Because
    # e.g. two sensors may have the same name, and thus the same description string, but
    # they should still produce distinct warnings. We have to turn other_data into a
    # string though, because otherwise its not hashable.
    columns_to_group_by = [
        "type_id",
        "type_name",
        "sensor_id",
        "batch_id",
        "other_data",
        "description",
        "priority",
    ]
    warnings = warnings.loc[:, columns_to_group_by + ["time_created"]]
    warnings["other_data"] = warnings["other_data"].apply(repr)
    warnings = (
        warnings.groupby(columns_to_group_by, dropna=False)
        .max()
        .reset_index()
        .sort_values(["time_created", "priority"], ascending=False)
    )
    return warnings


def format_warnings_json(warnings):
    """Convert a DataFrame of warnings into a list of dictionaries ready to be jsonified
    for Jinja.
    """
    warnings["time_string"] = warnings["time_created"].apply(
        lambda x: x.tz_convert(pytz.timezone("Europe/London")).strftime(
            "%a %d %b %y, %H:%M"
        )
    )
    # Converting to and from JSON ensures that we have a Python object that can be
    # cleanly converted to JSON by render_template.
    warnings_json = json.loads(warnings.to_json(orient="records"))
    return warnings_json


@blueprint.route("/index")
@login_required
def index():
    """
    Index page
    """
    dt_to = dt.datetime.now(dt.timezone.utc)
    dt_from_fortnightly = dt_to - dt.timedelta(days=14)
    dt_from_weekly = dt_to - dt.timedelta(days=7)
    dt_from_daily = dt_to - dt.timedelta(days=1)
    dt_from_6h = dt_to - dt.timedelta(hours=6)
    dt_from_hourly = dt_to - dt.timedelta(hours=2)

    # Get the largest timespan we need from the database. We can get the others by
    # slicing this, saving database queries.
    dt_from_min = min(
        dt_from_fortnightly, dt_from_weekly, dt_from_daily, dt_from_6h, dt_from_hourly
    )
    df_all = aranet_query(dt_from_min, dt_to)

    # weekly
    df_weekly = df_all.loc[df_all["timestamp"] >= dt_from_weekly, :]
    df_mean_hr_weekly = grp_per_hr_region(df_weekly)
    df_temp_weekly = bin_trh_data(
        df_mean_hr_weekly, TEMP_BINS, "temperature", expected_total=24 * 7
    )
    df_hum_weekly = bin_trh_data(
        df_mean_hr_weekly, HUM_BINS, "humidity", expected_total=24 * 7
    )
    df_vpd_weekly = bin_trh_data(
        df_mean_hr_weekly, VPD_BINS, "vpd", expected_total=24 * 7
    )
    weekly_temp_json = json_bin_counts(df_temp_weekly)
    weekly_hum_json = json_bin_counts(df_hum_weekly)
    weekly_vpd_json = json_bin_counts(df_vpd_weekly)

    # daily
    df_daily = df_weekly.loc[df_weekly["timestamp"] >= dt_from_daily, :]
    df_mean_hr_daily = grp_per_hr_region(df_daily)
    df_temp_daily = bin_trh_data(
        df_mean_hr_daily, TEMP_BINS, "temperature", expected_total=24
    )
    df_hum_daily = bin_trh_data(
        df_mean_hr_daily, HUM_BINS, "humidity", expected_total=24
    )
    df_vpd_daily = bin_trh_data(df_mean_hr_daily, VPD_BINS, "vpd", expected_total=24)
    daily_temp_json = json_bin_counts(df_temp_daily)
    daily_hum_json = json_bin_counts(df_hum_daily)
    daily_vpd_json = json_bin_counts(df_vpd_daily)

    # hourly
    df_hourly = df_daily.loc[df_daily["timestamp"] >= dt_from_hourly, :]
    if not df_hourly.empty:
        hourly_json = regional_mean_json(df_hourly)
    else:
        hourly_json = {}

    # 6h
    df_6h = df_daily.loc[df_daily["timestamp"] >= dt_from_6h, :]
    if not df_6h.empty:
        recent_minmax_json = regional_minmax_json(df_6h)
    else:
        recent_minmax_json = {}

    # fortnightly
    df_fortnightly = df_all.loc[df_all["timestamp"] >= dt_from_fortnightly, :]
    if not df_fortnightly.empty:
        # Sensor id locations:
        # 18: 16B1, 21: 1B2, 22: 29B2, 23: 16B4
        json_strat = stratification(df_fortnightly, (18, 21, 22, 23))
    else:
        json_strat = {}

    warning_categories, warning_categories_by_type = get_warning_categories()

    warnings = get_warnings(dt_from_daily)
    warnings["category_id"] = warnings["type_id"].apply(warning_categories_by_type.get)
    warnings_json = format_warnings_json(warnings)

    return render_template(
        "index.html",
        hourly_data=hourly_json,
        recent_minmax_data=recent_minmax_json,
        temperature_data=weekly_temp_json,
        humidity_data=weekly_hum_json,
        vpd_data=weekly_vpd_json,
        temperature_data_daily=daily_temp_json,
        humidity_data_daily=daily_hum_json,
        vpd_data_daily=daily_vpd_json,
        stratification=json_strat,
        dt_from=dt_from_weekly.strftime("%B %d, %Y"),
        dt_to=dt_to.strftime("%B %d, %Y"),
        warning_categories=warning_categories,
        warnings=warnings_json,
    )


@blueprint.route("/model")
@login_required
def model():
    """Unity model page."""
    return render_template("model.html")
