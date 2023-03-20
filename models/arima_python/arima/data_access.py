import logging
import psycopg2
import datetime
from .config import config
from jinjasql import JinjaSql
from six import string_types
from copy import deepcopy
import pandas as pd

logger = logging.getLogger(__name__)

data_config = config(section="data")


def open_connection():
    """
    Connect to the PostgreSQL database server.
    Returns a psycopg2 connection object if
    connection is successful.
    """
    conn = None
    try:
        # read DB connection parameters
        params = config()

        # connect to the PostreSQL server
        logger.info("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**params)

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
    finally:
        return conn


def close_connection(conn):
    """Close the PostgreSQL connection"""
    if conn is not None:
        conn.close()
        logger.info("Database connection closed.")


def get_data(query):
    """
    Fetch data from the DB based on the type of query.

    Parameters:
        query: JinjaSql.prepare_query object
    Returns:
        data: a pandas DataFrame where each row corresponds
            to a different row of the DB table
    """
    conn = None
    try:
        conn = open_connection()
        cur = conn.cursor()  # create a cursor
        cur.execute(query)
        data = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]  # get column names
        cur.close()  # close the communication with the PostgreSQL
        logger.info(f"Got data from {query} - returning {len(data)} rows")
        # convert the fetched list to a pandas dataframe
        data = pd.DataFrame(data, columns=colnames)
        remove_time_zone(data)  # all timestamps in the DB should be in UTC
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
    finally:
        close_connection(conn=conn)
    return data


def quote_sql_string(value):
    """
    If `value` is a string type, escapes single quotes in the string
    and returns the string enclosed in single quotes.
    """
    if isinstance(value, string_types):
        new_value = str(value)
        new_value = new_value.replace("'", "''")
        return "'{}'".format(new_value)
    return value


def get_sql_from_template(query, bind_params):
    if not bind_params:
        return query
    params = deepcopy(bind_params)
    for key, val in params.items():
        params[key] = quote_sql_string(val)
    return query % params


def get_temperature_humidity_data(delta_days, num_rows=None):
    """
    Fetch temperature and humidity data from the aranet_trh_data table
    of the DB over the specified time period, limited by the specified
    number of rows.

    Parameters:
        deltaDays: number of days into the past for which to retrieve the data.
        numRows: upper limit of number of rows to retrieve. Default is None (no
            upper limit is set).
    Returns:
        data: a pandas DataFrame where each row corresponds to a different row of the DB
            table, organised by the timestamp column of the aranet_trh_data table.
    """
    today = datetime.datetime.now(datetime.timezone.utc)
    delta = datetime.timedelta(days=delta_days)
    date_num_days_ago = today - delta
    params = {
        "timestamp": date_num_days_ago.strftime("%Y-%m-%d %H:%M:%S"),
        "numRows": num_rows,
    }
    if num_rows:
        transaction_template = """
        select
            sensors.name, aranet_trh_data.*
        from
            sensors, aranet_trh_data
        where
            (sensors.id = aranet_trh_data.sensor_id AND aranet_trh_data.timestamp >= {{ timestamp }})
        order by
            aranet_trh_data.timestamp asc
        limit
            {{ numRows }}
        """
    else:
        transaction_template = """
        select
            sensors.name, aranet_trh_data.*
        from
            sensors, aranet_trh_data
        where
            (sensors.id = aranet_trh_data.sensor_id AND aranet_trh_data.timestamp >= {{ timestamp }})
        order by
            aranet_trh_data.timestamp asc
        """
    j = JinjaSql(param_style="pyformat")
    query, bind_params = j.prepare_query(transaction_template, params)
    data = get_data(get_sql_from_template(query=query, bind_params=bind_params))
    logger.info("Temperature/Rel humidity data - head/tail:")
    logger.info(data.head(5))
    logger.info(data.tail(5))
    return data


def get_energy_data(delta_days, num_rows=None):
    """
    Fetch energy data from the utc_energy_data table
    over the specified time period, limited by the specified
    number of rows.

    Parameters:
        deltaDays: number of days into the past for which to retrieve the data.
        numRows: upper limit of number of rows to retrieve. Default is None (no
            upper limit is set).
    Returns:
        data: a pandas DataFrame where each row corresponds to a different row of the DB
            table, organised by the timestamp column of the utc_energy_data table.
    """
    today = datetime.datetime.now(datetime.timezone.utc)
    delta = datetime.timedelta(days=delta_days)
    date_num_days_ago = today - delta
    params = {
        "timestamp": date_num_days_ago.strftime("%Y-%m-%d %H:%M:%S"),
        "numRows": num_rows,
    }
    if num_rows:
        transaction_template = """
        select
            *
        from
            utc_energy_data
        where
            utc_energy_data.timestamp >= {{ timestamp }}
        order by
            utc_energy_data.timestamp asc
        limit
            {{ numRows }}
    """
    else:
        transaction_template = """
        select
            *
        from
            utc_energy_data
        where
            utc_energy_data.timestamp >= {{ timestamp }}
        order by
            utc_energy_data.timestamp asc
    """
    j = JinjaSql(param_style="pyformat")
    query, bind_params = j.prepare_query(transaction_template, params)
    data = get_data(get_sql_from_template(query=query, bind_params=bind_params))
    logger.info("Energy data - head/tail:")
    logger.info(data.head(5))
    logger.info(data.tail(5))
    return data


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
    if data_config["num_days_training"] > 365:
        logger.error(
            "The 'num_days_training' setting in config.ini cannot be set to a value greater than 365."
        )
        raise ValueError
    if data_config["num_days_training"] != 200:
        logger.warning(
            "The 'num_days_training' setting in config.ini has been set to something different than 200."
        )
    env_data = get_temperature_humidity_data(
        delta_days=data_config["num_days_training"], num_rows=num_rows
    )
    energy_data = get_energy_data(
        delta_days=data_config["num_days_training"], num_rows=num_rows
    )
    return env_data, energy_data
