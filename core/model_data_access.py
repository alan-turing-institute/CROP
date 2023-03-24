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

logger = logging.getLogger(__name__)


def get_sqlalchemy_session(connection_string=None, dbname=None):
    """
    For other functions in this module, if no session is provided as an argument,
    they will call this to get a session using default connection string.
    """
    if not connection_string:
        connection_string = SQL_CONNECTION_STRING
    if not dbname:
        dbname = SQL_DBNAME
    status, log, engine = connect_db(connection_string, dbname)
    session = session_open(engine)
    return session


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
    result = session.execute(query.statement).fetchall()
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
    result = session.execute(query.statement).fetchall()
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
    result = session.execute(query.statement).fetchall()
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
    result = session.execute(query.statement).fetchall()
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


def get_training_data(
    config_sections=None,
    delta_days=None,
    num_rows=None,
    session=None,
    arima_config=None,
):
    """Fetch data from one or more tables for training of the ARIMA model.

    Each output DataFrame can also be the result of joining two tables, as specified in
    the config.ini file.

    Args:
        config_sections (list of strings): A list of section names in the config.ini
            file corresponding to the tables and columns to fetch data from. Example:
            ["table1", "table2"]. If None, the default is ["env_data", "energy_data"].
        delta_days (int): Number of days in the past from which to retrieve data.
            Defaults to None.
        num_rows (int, optional): Number of rows to limit the data to. Defaults to None.
        session (_type_, optional): _description_. Defaults to None.
        arima_config: A function that can be called to return various sections of the
            Arima config.

    Returns:
        tuple: A tuple of pandas DataFrames, each corresponding to the data fetched from
            one of the specified tables. The DataFrames are sorted by the timestamp
            column.
    """
    if config_sections is None:
        config_sections = ["env_data", "energy_data"]

    # get number of training days
    if delta_days is None:
        num_days_training = arima_config(section="data")["num_days_training"]
    else:
        num_days_training = delta_days
    if num_days_training > 365:
        logger.error(
            "The 'num_days_training' setting in config.ini cannot be set to a "
            "value greater than 365."
        )
        raise ValueError
    elif num_days_training != 200:
        logger.warning(
            "The 'num_days_training' setting in config.ini has been set to something "
            "different than 200."
        )

    # get one table per section in the config.ini file.
    # each table can be produced by joining two tables, as specified in the config file.
    data_tables = []
    for section in config_sections:
        config_params = arima_config(section=section)
        # check that table class specified in config file is imported
        table_class_name = config_params["table_class"]
        if table_class_name not in globals():
            raise ImportError(
                f"Table class '{table_class_name}' not found. Make sure it's imported."
            )
        # get table class based on name
        table_class = globals()[table_class_name]
        columns = []
        for col in config_params["columns"].split(","):
            try:
                columns.append(getattr(table_class, col))
            # if column not in table class, try to find it in the join class
            except AttributeError:
                if "join_class" in config_params:
                    join_class = globals()[config_params["join_class"]]
                    columns.append(getattr(join_class, col))
                else:
                    raise AttributeError(
                        f"Attribute '{col}' not found in '{table_class}' or "
                        f"'{join_class}'"
                    )

        if not session:
            session = get_sqlalchemy_session()
        date_to = datetime.datetime.now()
        delta = datetime.timedelta(days=num_days_training)
        data_from = date_to - delta

        query = session.query(*columns).filter(table_class.timestamp > data_from)

        if "join_class" in config_params and "join_condition" in config_params:
            join_condition = eval(config_params["join_condition"])
            query = query.join(join_class, join_condition)

        query = query.order_by(asc(table_class.timestamp)).limit(num_rows)

        data = pd.read_sql(query.statement, query.session.bind)
        remove_time_zone(data)

        logger.info(f"{section} data - head/tail:")
        logger.info(data.head(5))
        logger.info(data.tail(5))
        if data.empty:
            logger.warning(f"{section} DataFrame is empty.")

        session_close(session)
        data_tables.append(data)

    return tuple(data_tables)
