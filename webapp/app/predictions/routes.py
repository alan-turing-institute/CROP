"""
A module for the prediction page actions
"""

import datetime as dt
import json
import logging

from flask import render_template, request
from flask_login import login_required
import pandas as pd
from sqlalchemy import and_

from app.predictions import blueprint
from cropcore.constants import (
    CONST_TIMESTAMP_FORMAT,
    ARIMA_MODEL_ID,
    BSTS_MODEL_ID,
    GES_MODEL_ID,
    GES_SENSOR_ID,
)
from cropcore import queries
from cropcore.structure import (
    ModelClass,
    ModelMeasureClass,
    ModelRunClass,
    ModelValueClass,
    ModelProductClass,
    ModelScenarioClass,
    ReadingsAranetTRHClass,
    SensorLocationClass,
    LocationClass,
    SensorClass,
)
from cropcore.structure import SQLA as db


def aranet_trh_query(dt_from, dt_to):
    """
    Performs a query for temperature and relative humidity data.

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
    Returns:
        df: a df with the queried data
    """
    locations_query = queries.latest_sensor_locations(db.session).subquery(
        "sensor_locations"
    )
    query = db.session.query(
        ReadingsAranetTRHClass.timestamp,
        ReadingsAranetTRHClass.sensor_id,
        ReadingsAranetTRHClass.temperature,
        ReadingsAranetTRHClass.humidity,
        LocationClass.zone,
    ).filter(
        and_(
            locations_query.c.location_id == LocationClass.id,
            ReadingsAranetTRHClass.sensor_id == locations_query.c.sensor_id,
            ReadingsAranetTRHClass.timestamp >= dt_from,
            ReadingsAranetTRHClass.timestamp <= dt_to,
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
        "Calling model %i with parameters %s %s"
        % (
            model_id,
            dt_from.strftime(CONST_TIMESTAMP_FORMAT),
            dt_to.strftime(CONST_TIMESTAMP_FORMAT),
        )
    )

    # subquery to get the last model run from a given model
    sbqr = (
        db.session.query(ModelRunClass)
        .filter(
            ModelRunClass.model_id == model_id,
            ModelRunClass.sensor_id == sensor_id,
        )
        .all()
    )
    if len(sbqr) > 0:
        sbqr = sbqr[-1]
    else:
        return None
    # query to get all the results from the model run in the subquery
    query = db.session.query(
        ModelClass.id,
        ModelClass.model_name,
        ModelRunClass.sensor_id,
        ModelMeasureClass.measure_name,
        ModelValueClass.prediction_value,
        ModelValueClass.prediction_index,
        ModelProductClass.run_id,
        ModelRunClass.time_created,
        ModelRunClass.time_forecast,
        ModelScenarioClass.ventilation_rate,
        ModelScenarioClass.num_dehumidifiers,
        ModelScenarioClass.lighting_shift,
        ModelScenarioClass.scenario_type,
    ).filter(
        and_(
            ModelClass.id == model_id,
            ModelRunClass.model_id == ModelClass.id,
            ModelRunClass.id == sbqr.id,
            ModelProductClass.run_id == ModelRunClass.id,
            ModelProductClass.measure_id == ModelMeasureClass.id,
            ModelValueClass.product_id == ModelProductClass.id,
            ModelRunClass.sensor_id == sensor_id,
            ModelRunClass.time_created >= dt_from,
            ModelRunClass.time_created <= dt_to,
            ModelMeasureClass.scenario_id == ModelScenarioClass.id,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)
    df["scenario_type"] = df["scenario_type"].astype(str)
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
    Function to return the JSON for the temperature related charts in the model run
    """
    # The shift_hours=1 accounts for df_arima starting its indexing from 1
    # instead of 0.
    df_arima = add_time_columns(df_arima, shift_hours=1)
    if len(df_arima) < 1:
        return "{}"
    json_str = (
        df_arima.groupby(["sensor_id", "measure_name", "run_id"], as_index=True)
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
        df.groupby(
            [
                "sensor_id",
                "measure_name",
                "run_id",
                "ventilation_rate",
                "num_dehumidifiers",
                "lighting_shift",
                "scenario_type",
            ],
            as_index=True,
        )
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


def recent_arima_sensors(timerange=dt.timedelta(days=5)):
    """Get the IDs of sensors for which there has been an Arima run in the last some
    time.
    """
    dt_from = dt.datetime.now() - timerange
    query = (
        db.session.query(ModelRunClass.sensor_id)
        .filter(ModelRunClass.time_created >= dt_from)
        .distinct()
    )
    ids = db.session.execute(query).fetchall()
    ids = [i[0] for i in ids]
    return ids


def arima_template():
    sensor_ids = recent_arima_sensors()
    dt_to = dt.datetime.now()
    dt_from = dt_to - dt.timedelta(days=3)

    data = {}

    for sensor_id in sensor_ids:
        # Model number 1 is Arima, 2 is BSTS, 3 is for GES.
        df_arima = model_query(dt_from, dt_to, ARIMA_MODEL_ID, sensor_id)
        if df_arima is not None and len(df_arima) > 0:
            json_arima = json_temp_arima(df_arima)
            # Get TRH data for the relevant period
            times = pd.to_datetime(df_arima["timestamp"])
            first_arima_time = times.min()
            last_arima_time = times.max()
            dt_from_z = first_arima_time - dt.timedelta(days=2)
            dt_to_z = last_arima_time
            json_trh = json_temp_trh(dt_from_z, dt_to_z)
            data[sensor_id] = {
                "arima": json.loads(json_arima),
                "trh": json.loads(json_trh),
            }
        else:
            logging.warn(f"No Arima forecast available for sensor {sensor_id}")

    valid_sensor_ids = tuple(data.keys())
    return render_template(
        "arima.html", data=json.dumps(data), sensor_ids=valid_sensor_ids
    )


def ges_template():
    # These dates only control the window within which the prediction time
    # should be, not the time window that gets plotted.
    dt_to = dt.datetime.now()
    dt_from = dt_to - dt.timedelta(days=3)
    df_ges = model_query(dt_from, dt_to, GES_MODEL_ID, GES_SENSOR_ID)
    if df_ges is not None and len(df_ges) > 0:
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
    else:
        json_ges = {}
        json_trh = {}
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
