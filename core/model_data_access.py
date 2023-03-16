"""
Combined data access module for GES and ARIMA models
"""

import logging
import sys
import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import desc, asc, exc, func

from models.ges.ges.config import config as ges_config
from models.arima_python.arima.config import config as arima_config

from cropcore.db import connect_db, session_open, session_close
from cropcore.structure import (
    # arima
    SensorClass,
    ReadingsAranetTRHClass,
    ReadingsEnergyClass,
    # ges
    ReadingsWeatherClass,
    WeatherForecastsClass,
    ModelRunClass,
    ModelProductClass,
    ModelValueClass,
)
from cropcore.constants import SQL_CONNECTION_STRING, SQL_DBNAME
from models.ges.ges.ges_utils import get_sqlalchemy_session

logger = logging.getLogger(__name__)

path_conf = ges_config(section="paths")
data_dir_ges = Path(path_conf["data_dir"]) # unused

# ges ---------------------------------------------------------------------

def print_rows_head(rows, numrows=0):
    logging.info("Printing:{0} of {1}".format(numrows, len(rows)))
    if numrows == 0:
        for row in rows[: len(rows)]:
            logging.info(row)
    else:
        for row in rows[:numrows]:
            logging.info(row)


def get_days_weather(num_days=2, num_rows=5, session=None):
    """
    Get 5 rows of weather data [(timestamp:datetime, temp:float, humid:float),...]
    """
    if not session:
        session = get_sqlalchemy_session()
    date_to = datetime.datetime.now()
    delta = datetime.timedelta(days=num_days)
    date_from = date_to - delta
    query = (
        session.query(
            ReadingsWeatherClass.timestamp,
            ReadingsWeatherClass.temperature,
            ReadingsWeatherClass.relative_humidity,
        )
        .filter(ReadingsWeatherClass.timestamp > date_from)
        .order_by(asc(ReadingsWeatherClass.timestamp))
        .limit(num_rows)
    )
    result = session.execute(query).fetchall()
    session_close(session)
    return result


def get_days_weather_forecast(num_days=2, session=None):
    if not session:
        session = get_sqlalchemy_session()
    date_from = datetime.datetime.now()
    delta = datetime.timedelta(days=num_days)
    date_to = date_from + delta
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


def get_days_humidity_temperature(
    delta_days=10, num_rows=5, sensor_id=27, session=None
):
    if not session:
        session = get_sqlalchemy_session()
    date_to = datetime.datetime.now()
    delta = datetime.timedelta(days=delta_days)
    date_from = date_to - delta
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


def get_days_humidity(delta_days=10, num_rows=5, sensor_id=27, session=None):
    """
    almost the same as get_days_humidity - just run that and get the first
    and third elements of the output tuples.
    """
    result = get_days_humidity_temperature(delta_days, num_rows, sensor_id, session)
    return [(r[0], r[2]) for r in result]


def get_datapoint_humidity(sensor_id=27, num_rows=1, session=None):
    if not session:
        session = get_sqlalchemy_session()
    query = (
        session.query(ReadingsAranetTRHClass.timestamp, ReadingsAranetTRHClass.humidity)
        .filter(ReadingsAranetTRHClass.sensor_id == sensor_id)
        .order_by(desc(ReadingsAranetTRHClass.timestamp))
        .limit(num_rows)
    )
    result = session.execute(query).fetchall()
    session_close(session)
    return result


def get_datapoint(filepath=None, **kwargs):
    if filepath:
        LastDataPoint = pd.read_csv(filepath)
        jj = np.size(LastDataPoint, 1)
        if jj > 1:
            DataPoint = float(LastDataPoint[str(jj)])
        else:
            DataPoint = 0.5  # dummy value
        return DataPoint
    else:
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


# arima -----------------------------------------------------------------------

def remove_time_zone(dataframe: pd.DataFrame):
    """
    Remove timezone information from datetime columns.
    Note that all timestamps in the SQL database should be UTC.

    Parameters:
        dataframe: pandas DataFrame
    """
    new_dataframe = dataframe.select_dtypes("datetimetz")
    if not new_dataframe.empty:
        colnames = new_dataframe.columns.to_list()
        for column in colnames:
            dataframe[column] = pd.to_datetime(dataframe[column]).dt.tz_localize(None)
            
def get_temperature_humidity_data(delta_days, num_rows=None, session=None):
    """Fetch temperature and humidity data from the aranet_trh_data table
    over the specified time period, limited by the specified number of rows.

     Args:
        delta_days (int): Number of days in the past from which to retrieve data. Defaults to 100.
        num_rows (int): Number of rows to limit the data to. 
        session (_type_): _description_. Defaults to None.

    Returns:
        data: A pandas dataframe with each row corresponding to a different row of the DB table, 
        sorted by the timestamp column of the utc_energy_data table.
    """
    
    if not session:
        session = get_sqlalchemy_session()
    date_to = datetime.datetime.now()
    delta = datetime.timedelta(days=delta_days)
    data_from = date_to - delta
    query = (
        session.query(
            SensorClass.name,
            ReadingsAranetTRHClass.id,
            ReadingsAranetTRHClass.sensor_id,
            ReadingsAranetTRHClass.timestamp,
            ReadingsAranetTRHClass.temperature,
            ReadingsAranetTRHClass.humidity,
            ReadingsAranetTRHClass.time_created,
            ReadingsAranetTRHClass.time_updated
        )
        .join(SensorClass, SensorClass.id == ReadingsAranetTRHClass.sensor_id)
        .filter(ReadingsAranetTRHClass.timestamp > data_from)
        .order_by(asc(ReadingsAranetTRHClass.timestamp))
        .limit(num_rows)
    )
    data = pd.read_sql(query.statement, query.session.bind)
    remove_time_zone(data)
    
    logger.info("Temperature and humidity data - head/tail:")
    logger.info(data.head(5))
    logger.info(data.tail(5))
    
    session_close(session)
    return data
            
def get_energy_data(delta_days, num_rows=None, session=None):
    """ Fetch energy data from the utc_energy_data table
    over the specified time period, limited by the specified
    number of rows.

    Args:
        delta_days (int): Number of days in the past from which to retrieve data. Defaults to 100.
        num_rows (int): Number of rows to limit the data to.
        session (_type_): _description_. Defaults to None.

    Returns:
        data: A pandas dataframe with each row corresponding to a different row of the DB table, 
        sorted by the timestamp column of the utc_energy_data table.
    """
    if not session:
        session = get_sqlalchemy_session()
    date_to = datetime.datetime.now()
    delta = datetime.timedelta(days=delta_days)
    data_from = date_to - delta
    query = (
        session.query(
            ReadingsEnergyClass.timestamp,
            ReadingsEnergyClass.electricity_consumption,
            ReadingsEnergyClass.time_created,
            ReadingsEnergyClass.time_updated,
            ReadingsEnergyClass.sensor_id,
            ReadingsEnergyClass.id
            )
        .filter(ReadingsEnergyClass.timestamp > data_from)
        .order_by(asc(ReadingsEnergyClass.timestamp))
        .limit(num_rows)
    )
    data = pd.read_sql(query.statement, query.session.bind)
    remove_time_zone(data)
    
    logger.info("Energy data - head/tail:")
    logger.info(data.head(5))
    logger.info(data.tail(5))
    
    session_close(session)
    return data

def get_training_data(num_rows=None):
    """
    Fetch temperature and humidity data from the aranet_trh_data table
    and energy data from the utc_energy_data table for training of the
    ARIMA model.
    The number of days into the past for which to retrieve data from the
    DB is specified through "num_days_training" in the config.ini file.

    Parameters:
        numRows: upper limit of number of rows to retrieve. Default is None (no
            upper limit is set).
    Returns:
        env_data: pandas DataFrame containing the temperature and humidity data. Each row
            corresponds to a different row in the aranet_trh_data table. Organised
            by the timestamp column of the aranet_trh_data table.
        energy_data: pandas DataFrame containing the energy data. Each row corresponds
            to a different row in the utc_energy_data table. Organised
            by the timestamp column of the utc_energy_data table.
    """
    params = arima_config(section="data")
    num_days_training = params["num_days_training"]
    if num_days_training != 200:
        logger.warning(
            "The 'num_days_training' setting in config.ini has been set to something different than 200."
        )
    env_data = get_temperature_humidity_data(
        delta_days=num_days_training, num_rows=num_rows
    )
    energy_data = get_energy_data(delta_days=num_days_training, num_rows=num_rows)
    return env_data, energy_data