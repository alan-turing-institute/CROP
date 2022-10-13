"""
A module for the prediction page actions
"""

import logging
import copy
import datetime as dt
import pandas as pd
from pandas.core.frame import DataFrame


from app.predictions import blueprint
from flask import request, render_template
from flask_login import login_required

from sqlalchemy import and_, func

from core.structure import (
    ModelClass,
    ModelMeasureClass,
    ModelRunClass,
    ModelValueClass,
    ModelProductClass,
    TestModelClass,
    TestModelMeasureClass,
    TestModelRunClass,
    TestModelValueClass,
    TestModelProductClass,
    ReadingsAranetTRHClass,
    SensorLocationClass,
    LocationClass,
    SensorClass,
)

from core.structure import SQLA as db
from core.constants import CONST_TIMESTAMP_FORMAT

from core.utils import filter_latest_sensor_location


def aranet_trh_query(dt_from, dt_to):
    """
    Performs a query for temperature and relative humidity data.

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
    Returns:
        df: a df with the queried data
    """
    query = db.session.query(
        ReadingsAranetTRHClass.timestamp,
        ReadingsAranetTRHClass.sensor_id,
        ReadingsAranetTRHClass.temperature,
        ReadingsAranetTRHClass.humidity,
        LocationClass.zone,
    ).filter(
        and_(
            SensorLocationClass.location_id == LocationClass.id,
            ReadingsAranetTRHClass.sensor_id == SensorClass.id,
            ReadingsAranetTRHClass.sensor_id == SensorLocationClass.sensor_id,
            ReadingsAranetTRHClass.timestamp >= dt_from,
            ReadingsAranetTRHClass.timestamp <= dt_to,
            filter_latest_sensor_location(db),
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    logging.info("Total number of records found: %d" % (len(df.index)))

    if df.empty:
        logging.debug("WARNING: Query returned empty")

    return df


def model_query(dt_from, dt_to, model_id, sensor_id):
    """
    Performs a query for a prediction model.

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
        model_id: id for a particular model
    Returns:
        df: a df with the queried data
    """
    logging.info(
        "Calling arima model with parameters %s %s"
        % (
            dt_from.strftime(CONST_TIMESTAMP_FORMAT),
            dt_to.strftime(CONST_TIMESTAMP_FORMAT),
        )
    )

    model_class = ModelClass
    model_measure_class = ModelMeasureClass
    model_run_class = ModelRunClass
    model_value_class = ModelValueClass
    model_product_class = ModelProductClass

    # subquery to get the last model run from a given model
    sbqr = (
        db.session.query(model_run_class)
        .filter(
            model_run_class.model_id == model_id,
            model_run_class.sensor_id == sensor_id,
        )
        .all()[-1]
    )

    # query to get all the results from the model run in the subquery
    query = db.session.query(
        model_class.id,
        model_class.model_name,
        model_run_class.sensor_id,
        model_measure_class.measure_name,
        model_value_class.prediction_value,
        model_value_class.prediction_index,
        model_product_class.run_id,
        model_run_class.time_created,
        model_run_class.time_forecast,
    ).filter(
        and_(
            model_class.id == model_id,
            model_run_class.model_id == model_class.id,
            model_run_class.id == sbqr.id,
            model_product_class.run_id == model_run_class.id,
            model_product_class.measure_id == model_measure_class.id,
            model_value_class.product_id == model_product_class.id,
            model_run_class.sensor_id == sensor_id,
            model_run_class.time_created >= dt_from,
            model_run_class.time_created <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    logging.info("Total number of records found: %d" % (len(df.index)))

    if df.empty:
        logging.debug("WARNING: Query returned empty")

    return df


def resample(df):
    """
    Resamples (date per hour) to a dataframe.

    Arguments:
        temp_df: dataframe with temperature assign to bins
        bins: temperature or humidity bins as a list
    Returns:
        temp_df: the df with grouped bins
    """

    # Reseting index
    df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)
    df_grp_hr = (
        df.groupby("sensor_id")
        .resample("H", on="timestamp")
        .agg({"temperature": "mean", "humidity": "mean"})
        .reset_index()
    )

    return df_grp_hr


def add_time_columns(df, shift_hours=0):
    """Create timestamps from prediction index and convert date to string."""
    time_ = []
    timestamp_ = []
    for i in range(len(df)):
        pred_id = int(df["prediction_index"][i])
        pred_time = df["time_forecast"][i] + dt.timedelta(hours=pred_id - shift_hours)
        format_time = pred_time.strftime("%d-%m-%Y %H:%M:%S")
        time_.append(format_time)
        timestamp_.append(pred_time)
    df["time"] = time_
    df["timestamp"] = timestamp_
    return df


def json_temp_arima(df_arima):
    """
    Function to return the JSON for the temperature related
    charts in the model run

    """
    # The shift_hours=1 accounts for df_arima starting its indexing from 1
    # instead of 0.
    df_arima = add_time_columns(df_arima, shift_hours=1)
    json_str = (
        df_arima.groupby(
            ["sensor_id", "measure_name", "run_id"], as_index=True
        )  # "measure_name"
        .apply(
            lambda x: x[
                [
                    "prediction_value",
                    "prediction_index",
                    "run_id",
                    "time",
                    "timestamp",
                ]
            ].to_dict(orient="records")
        )
        .reset_index()
        .rename(columns={0: "Values"})
        .to_json(orient="records")
    )
    return json_str


def json_temp_trh(dt_from_daily, dt_to):
    df = aranet_trh_query(dt_from_daily, dt_to)

    if not df.empty:
        # resample T&RH data per hour
        df_grp_hr = resample(df)

        time_ = []
        for i in range(len(df_grp_hr)):
            time = df_grp_hr["timestamp"][i]
            format_time = time.strftime("%d-%m-%Y %H:%M:%S")
            time_.append(format_time)

        df_grp_hr["time"] = time_

        # .groupby('sensor_id').resample('H', on='timestamp').agg({'temperature':'mean', 'humidity':'mean'})
        return (
            df_grp_hr.groupby(["sensor_id"], as_index=True)  # "measure_name"
            .apply(
                lambda x: x[["temperature", "humidity", "time", "timestamp"]].to_dict(
                    orient="records"
                )
            )
            .reset_index()
            .rename(columns={0: "Values"})
            .to_json(orient="records")
        )
    else:
        return {}


def json_temp_ges(df):
    """
    Function to return the JSON for the temperature related charts in the GES
    model run.
    """
    json_str = (
        df.groupby(["sensor_id", "measure_name", "run_id"], as_index=True)
        .apply(
            lambda x: x[
                [
                    "prediction_value",
                    "prediction_index",
                    "run_id",
                    "time",
                    "timestamp",
                ]
            ].to_dict(orient="records")
        )
        .reset_index()
        .rename(columns={0: "Values"})
        .to_json(orient="records")
    )
    return json_str


def arima_template():
    # arima data
    # dt_to = dt.datetime(2021, 12, 4, 00, 00)  # dt.datetime.now()
    dt_to = dt.datetime.now()
    dt_from = dt_to - dt.timedelta(days=3)

    # Model number 1 is Arima, 2 is BSTS, 3 is for GES.
    df_arima_18 = model_query(dt_from, dt_to, 1, 18)
    df_arima_23 = model_query(dt_from, dt_to, 1, 23)
    df_arima_27 = model_query(dt_from, dt_to, 1, 27)

    df_arima_ = df_arima_23.append(df_arima_18, ignore_index=True)
    df_arima = df_arima_.append(df_arima_27, ignore_index=True)

    json_arima = json_temp_arima(df_arima)

    unique_time_forecast = df_arima["time_forecast"].unique()
    date_time = pd.to_datetime(unique_time_forecast[0])
    dt_to_z = date_time + dt.timedelta(days=+3)
    dt_from_z = dt_to_z + dt.timedelta(days=-5)
    json_trh = json_temp_trh(dt_from_z, dt_to_z)

    unique_time_forecast_18 = df_arima_18["time_forecast"].unique()
    date_time_18 = pd.to_datetime(unique_time_forecast_18[0])
    dt_to_z_18 = date_time_18 + dt.timedelta(days=+3)
    dt_from_z_18 = dt_to_z_18 + dt.timedelta(days=-5)
    json_trh_18 = json_temp_trh(dt_from_z_18, dt_to_z_18)

    unique_time_forecast_23 = df_arima_23["time_forecast"].unique()
    date_time_23 = pd.to_datetime(unique_time_forecast_23[0])
    dt_to_z_23 = date_time_23 + dt.timedelta(days=+3)
    dt_from_z_23 = dt_to_z_23 + dt.timedelta(days=-5)
    json_trh_23 = json_temp_trh(dt_from_z_23, dt_to_z_23)

    unique_time_forecast_27 = df_arima_27["time_forecast"].unique()
    date_time_27 = pd.to_datetime(unique_time_forecast_27[0])
    dt_to_z_27 = date_time_27 + dt.timedelta(days=+3)
    dt_from_z_27 = dt_to_z_27 + dt.timedelta(days=-5)
    json_trh_27 = json_temp_trh(dt_from_z_27, dt_to_z_27)

    return render_template(
        "arima.html",
        json_arima_f=json_arima,
        json_trh_f=json_trh,
        json_trh_18_f=json_trh_18,
        json_trh_23_f=json_trh_23,
        json_trh_27_f=json_trh_27,
    )


def ges_template():
    # These dates only control the window within which the prediction time
    # should be, not the time window that gets plotted.
    dt_to = dt.datetime.now()
    dt_from = dt_to - dt.timedelta(days=3)
    df_ges = model_query(dt_from, dt_to, 3, 27)
    # TODO This is a hard coded constant for now, marking the length of the
    # calibration period, because this data is lacking in the DB.
    time_shift = 24 * 10 - 1
    df_ges = add_time_columns(df_ges, time_shift)
    # Crop the data to a certain time window.
    unique_time_forecast = df_ges["time_forecast"].unique()
    forecast_time = pd.to_datetime(unique_time_forecast[0])
    start_time = forecast_time - dt.timedelta(days=3)
    end_time = df_ges["timestamp"].max()
    df_ges = df_ges[start_time <= df_ges["timestamp"]]
    json_ges = json_temp_ges(df_ges)
    # Get Aranet T&RH data within that window.
    json_trh = json_temp_trh(start_time, end_time)
    return render_template(
        "ges.html",
        json_ges_f=json_ges,
        json_trh_f=json_trh,
    )


@blueprint.route("/<template>")
@login_required
def route_template(template, methods=["GET"]):
    if template == "arima":
        return arima_template()
    elif template == "ges":
        return ges_template()
    else:
        return render_template(template + ".html")
