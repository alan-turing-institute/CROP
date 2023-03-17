import sys
import logging
from pathlib import Path
from sqlalchemy import desc, asc, exc

from freezegun import freeze_time

import datetime

import numpy as np
import pandas as pd
from .config import config

from cropcore.db import connect_db, session_open, session_close
from cropcore.structure import (
    ReadingsWeatherClass,
    WeatherForecastsClass,
    ReadingsAranetTRHClass,
    ModelRunClass,
    ModelProductClass,
    ModelValueClass,
)
from cropcore.constants import SQL_CONNECTION_STRING, SQL_DBNAME, CONST_NOWTIME
from .ges_utils import get_sqlalchemy_session

path_conf = config(section="paths")
data_dir = Path(path_conf["data_dir"])


def print_rows_head(rows, numrows=0):
    logging.info("Printing:{0} of {1}".format(numrows, len(rows)))
    if numrows == 0:
        for row in rows[: len(rows)]:
            logging.info(row)
    else:
        for row in rows[:numrows]:
            logging.info(row)

@freeze_time(CONST_NOWTIME)
def get_days_weather(num_days=2, num_rows=5, session=None):
    """
    Get 5 rows of weather data [(timestamp:datetime, temp:float, humid:float),...]
    """
    if not session:
        session = get_sqlalchemy_session()
    date_to = datetime.datetime.now()
    delta = datetime.timedelta(days=num_days)
    date_from = date_to - delta
    print(f"Getting weather data for {date_from} to {date_to}")
    query = (
        session.query(
            ReadingsWeatherClass.timestamp,
            ReadingsWeatherClass.temperature,
            ReadingsWeatherClass.relative_humidity,
        )
        .filter(ReadingsWeatherClass.timestamp > date_from)
        .filter(ReadingsWeatherClass.timestamp < date_to)
        .order_by(asc(ReadingsWeatherClass.timestamp))
        .limit(num_rows)
    )
    result = session.execute(query).fetchall()
    session_close(session)
    return result

@freeze_time(CONST_NOWTIME)
def get_days_weather_forecast(num_days=2, session=None):
    if not session:
        session = get_sqlalchemy_session()
    date_from = datetime.datetime.now()
    delta = datetime.timedelta(days=num_days)
    date_to = date_from + delta
    print(f"Getting weather forecast data for {date_from} to {date_to}")
    # allow for a delay of 24 hours from current time to ensure that there are
    # no gaps between historical weather data (retrieved from table iweather)
    # and forecast weather data (retrieved from table weather_forecast)
    date_from = date_from - datetime.timedelta(hours=24)
    query = (
        session.query(
            WeatherForecastsClass.timestamp,
            WeatherForecastsClass.temperature,
            WeatherForecastsClass.relative_humidity,
            WeatherForecastsClass.time_created,
        )
        .filter(WeatherForecastsClass.timestamp > date_from)
        .filter(WeatherForecastsClass.timestamp < date_to)
        .order_by(
            WeatherForecastsClass.timestamp, desc(WeatherForecastsClass.time_created)
        )
        .distinct(WeatherForecastsClass.timestamp)
    )
    result = session.execute(query).fetchall()
    session_close(session)
    # drop the time_created (the last element) from each row
    return [r[:3] for r in result]

@freeze_time(CONST_NOWTIME)
def get_days_humidity_temperature(
    delta_days=10, num_rows=5, sensor_id=27, session=None
):
    if not session:
        session = get_sqlalchemy_session()
    date_to = datetime.datetime.now()
    delta = datetime.timedelta(days=delta_days)
    date_from = date_to - delta
    print(f"Getting TRH data for {date_from} to {date_to}")
    query = (
        session.query(
            ReadingsAranetTRHClass.timestamp,
            ReadingsAranetTRHClass.temperature,
            ReadingsAranetTRHClass.humidity,
        )
        .filter(ReadingsAranetTRHClass.sensor_id == sensor_id)
        .filter(ReadingsAranetTRHClass.timestamp > date_from)
        .limit(num_rows)
    )
    result = session.execute(query).fetchall()
    session_close(session)
    return result

@freeze_time(CONST_NOWTIME)
def get_days_humidity(delta_days=10, num_rows=5, sensor_id=27, session=None):
    """
    almost the same as get_days_humidity - just run that and get the first
    and third elements of the output tuples.
    """
    result = get_days_humidity_temperature(delta_days, num_rows, sensor_id, session)
    return [(r[0], r[2]) for r in result]

@freeze_time(CONST_NOWTIME)
def get_datapoint_humidity(sensor_id=27, num_rows=1, session=None):
    if not session:
        session = get_sqlalchemy_session()
    query = (
        session.query(ReadingsAranetTRHClass.timestamp, ReadingsAranetTRHClass.humidity)
        .filter(ReadingsAranetTRHClass.sensor_id == sensor_id)
        .order_by(desc(ReadingsAranetTRHClass.timestamp))
        .limit(num_rows)
    )
    print("Getting datapoint humidity. Why?")
    result = session.execute(query).fetchall()
    session_close(session)
    return result


def get_datapoint(filepath=None, **kwargs):
    if filepath:
        print("Getting datapoint from filepath")
        LastDataPoint = pd.read_csv(filepath)
        jj = np.size(LastDataPoint, 1)
        if jj > 1:
            DataPoint = float(LastDataPoint[str(jj)])
        else:
            DataPoint = 0.5  # dummy value
        return DataPoint
    else:
        print("Getting datapoint humidity from db")
        dp_database = np.asarray(get_datapoint_humidity(**kwargs))[0, 1]
        return dp_database


def insert_model_run(sensor_id=None, model_id=None, time_forecast=None, session=None):
    if not session:
        session = get_sqlalchemy_session()
    if sensor_id is not None and model_id is not None and time_forecast is not None:
        mr = ModelRunClass(
            sensor_id=sensor_id, model_id=model_id, time_forecast=time_forecast
        )
        try:
            session.add(mr)
            session.commit()
            session.refresh(mr)
            run_id = mr.id
            print(f"Inserted model run {run_id}")
            return run_id
        except exc.SQLAlchemyError:
            session.rollback()
    session.close()


def insert_model_product(run_id=None, measure_id=None, session=None):
    if not session:
        session = get_sqlalchemy_session()
    if run_id is not None and measure_id is not None:
        mp = ModelProductClass(run_id=run_id, measure_id=measure_id)
        try:
            session.add(mp)
            session.commit()
            session.refresh(mp)
            product_id = mp.id
            print(f"Inserting model product {product_id}")
            return product_id
        except exc.SQLAlchemyError:
            session.rollback()
    session.close()


def insert_model_predictions(predictions=None, session=None):
    if not session:
        session = get_sqlalchemy_session()
    num_rows_inserted = 0
    if predictions is not None:
        print(f"Inserting {len(predictions)} model prediction values")
        if len(predictions) > 0:
            for prediction in predictions:
                mv = ModelValueClass(
                    product_id=prediction[0],
                    prediction_value=prediction[1],
                    prediction_index=prediction[2],
                )
                try:
                    session.add(mv)
                    session.commit()
                    num_rows_inserted += 1
                except exc.SQLAlchemyError as e:
                    print(f"Error adding row: {e}")
                    session.rollback()
                    break
    session.close()
    print(f"Inserted {num_rows_inserted} value predictions")
    return num_rows_inserted
