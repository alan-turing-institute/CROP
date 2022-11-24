import logging
import psycopg2
import datetime
from .config import config
from jinjasql import JinjaSql
from six import string_types
from copy import deepcopy


def openConnection():
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
        logging.info("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**params)

    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(error)
    finally:
        return conn


def closeConnection(conn):
    """Close the PostgreSQL connection"""
    if conn is not None:
        conn.close()
        logging.info("Database connection closed.")


def printRowsHead(rows, numrows=0):
    """Log the number of rows retrieved from the database"""
    logging.info("Printing:{0} of {1}".format(numrows, len(rows)))
    if numrows == 0:
        for row in rows[: len(rows)]:
            logging.info(row)
    else:
        for row in rows[:numrows]:
            logging.info(row)


def getData(query):
    """
    Fetch data from the DB based on the type of query.

    Parameters:
        query: JinjaSql.prepare_query object
    Returns:
        rows: a list where each entry corresponds to a
            different row of the DB table
    """
    conn = None
    try:
        conn = openConnection()
        cur = conn.cursor()  # create a cursor
        cur.execute(query)
        rows = cur.fetchall()
        printRowsHead(rows, numrows=10)
        cur.close()  # close the communication with the PostgreSQL
        logging.info(f"Got data from {query} - returning {len(rows)} rows")
    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(error)
    finally:
        closeConnection(conn=conn)
    return rows


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


def getTemperatureHumidityData(deltaDays, numRows=None):
    """
    Fetch temperature and humidity data from the aranet_trh_data table
    of the DB over the specified time period, limited by the specified
    number of rows.

    Parameters:
        deltaDays: number of days into the past for which to retrieve the data.
        numRows: upper limit of number of rows to retrieve. Default is None (no
            upper limit is set).
    Returns:
        data: a list where each entry corresponds to a different row of the DB
            table, organised by the timestamp column of the aranet_trh_data table.
    """
    today = datetime.datetime.now()
    delta = datetime.timedelta(days=deltaDays)
    dateNumDaysAgo = today - delta
    params = {
        "timestamp": dateNumDaysAgo.strftime("%Y-%m-%d %H:%M:%S"),
        "numRows": numRows,
    }
    if numRows:
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
    return getData(get_sql_from_template(query=query, bind_params=bind_params))


def getEnergyData(deltaDays, numRows=None):
    """
    Fetch energy data from the utc_energy_data table
    over the specified time period, limited by the specified
    number of rows.

    Parameters:
        deltaDays: number of days into the past for which to retrieve the data.
        numRows: upper limit of number of rows to retrieve. Default is None (no
            upper limit is set).
    Returns:
        data: a list where each entry corresponds to a different row of the DB
            table, organised by the timestamp column of the utc_energy_data table.
    """
    today = datetime.datetime.now()
    delta = datetime.timedelta(days=deltaDays)
    dateNumDaysAgo = today - delta
    params = {
        "timestamp": dateNumDaysAgo.strftime("%Y-%m-%d %H:%M:%S"),
        "numRows": numRows,
    }
    if numRows:
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
    return getData(get_sql_from_template(query=query, bind_params=bind_params))


def getTrainingData(numRows=None):
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
        env_data: list containing the temperature and humidity data. Each entry
            corresponds to a different row in the aranet_trh_data table. Organised
            by the timestamp column of the aranet_trh_data table.
        energy_data: list containing the energy data. Each entry corresponds
            to a different row in the utc_energy_data table. Organised
            by the timestamp column of the utc_energy_data table.
    """
    params = config(section="constants")
    num_days_training = params["num_days_training"]
    env_data = getTemperatureHumidityData(deltaDays=num_days_training, numRows=numRows)
    energy_data = getEnergyData(deltaDays=num_days_training, numRows=numRows)
    return env_data, energy_data
