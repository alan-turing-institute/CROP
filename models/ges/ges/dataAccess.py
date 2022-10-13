import logging
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
import datetime
from jinjasql import JinjaSql
from six import string_types
from copy import deepcopy
import numpy as np
import pandas as pd
from .config import config

path_conf = config(section="paths")
data_dir = Path(path_conf["data_dir"])


def openConnection():
    """Connect to the PostgreSQL database server"""
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        logging.info("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**params)

    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(error)
    finally:
        return conn


def closeConnection(conn):
    if conn is not None:
        conn.close()
        logging.info("Database connection closed.")


def connect():
    """Connect to the PostgreSQL database server"""
    conn = None
    try:
        conn = openConnection()
        if conn is not None:
            # create a cursor
            cur = conn.cursor()
            cur.execute("SELECT version()")
            db_version = cur.fetchone()

            # execute a statement
            logging.info("PostgreSQL database version:{0}".format(db_version))

            # close the communication with the PostgreSQL
            cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(error)
    finally:
        closeConnection(conn=conn)


def printRowsHead(rows, numrows=0):
    logging.info("Printing:{0} of {1}".format(numrows, len(rows)))
    if numrows == 0:
        for row in rows[: len(rows)]:
            logging.info(row)
    else:
        for row in rows[:numrows]:
            logging.info(row)


def deleteData(query):
    result = []
    conn = None
    try:
        conn = openConnection()
        if conn is not None:
            cur = conn.cursor()
            cur.execute(query)
            conn.commit()
            result = cur.fetchall()
            cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(error)
    finally:
        closeConnection(conn=conn)
        return len(result)


def getData(query):
    conn = None
    try:
        conn = openConnection()
        if conn is not None:
            # create a cursor
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            printRowsHead(rows, numrows=10)

            # close the communication with the PostgreSQL
            cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(error)
    finally:
        closeConnection(conn=conn)
    print(f"Got data from {query} - returning {len(rows)} rows")
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


def getDaysWeather(numDays=2, numRows=5):
    today = datetime.datetime.now()
    delta = datetime.timedelta(days=numDays)
    dateNumDaysAgo = today - delta
    params = {
        "timestamp": dateNumDaysAgo.strftime("%Y-%m-%d %H:%M:%S"),
        "numRows": numRows,
    }

    weather_transaction_template = """
  select
    timestamp, temperature, relative_humidity
  from
    iweather
  where timestamp >= {{ timestamp }}
  order by
    timestamp asc
  limit {{ numRows }}
  """
    j = JinjaSql(param_style="pyformat")
    query, bind_params = j.prepare_query(weather_transaction_template, params)
    return getData(get_sql_from_template(query=query, bind_params=bind_params))


def getDaysWeatherForecast(numDays=2):
    """
    Gets hourly weather forecast data (temperature and relative humidity)
    from the database table "weather_forecast".
    The function retrieves the latest weather forecasts as these are likely
    to be more accurate than older weather forecasts.

    Parameters:
        numDays: number of days into the future for which to retrieve hourly
            weather forecasts. Default is 2 (only 48h forecasts are available
            in the table).
    Returns:
        data: list of hourly weather forecasts (each entry corresponds to a
            different forecasted time). The list contains: forcasted time,
            temperature (in Celsius) and relative humidity (percentage)
    """
    today = datetime.datetime.now()
    delta = datetime.timedelta(days=numDays)
    dateNumDaysForecast = today + delta
    # allow for a delay of 24 hours from current time to ensure that there are
    # no gaps between historical weather data (retrieved from table iweather)
    # and forecast weather data (retrieved from table weather_forecast)
    today = today - datetime.timedelta(hours=24)
    params = {
        "timeStampStart": today.strftime("%Y-%m-%d %H:%M:%S"),
        "timeStampEnd": dateNumDaysForecast.strftime("%Y-%m-%d %H:%M:%S"),
    }
    # retrieve timestamp (forecasted time), temperature, relative_humidity and time_created from database
    # sort out data in descending order of time_created (i.e. when the forecast was made)
    weather_transaction_template = """
  select
    timestamp, temperature, relative_humidity, time_created
  from
    weather_forecast
  where timestamp >= {{ timeStampStart }} and timestamp <= {{ timeStampEnd }}
  order by
    time_created desc
  """
    j = JinjaSql(param_style="pyformat")
    query, bind_params = j.prepare_query(weather_transaction_template, params)
    data = getData(get_sql_from_template(query=query, bind_params=bind_params))
    # convert list to pandas DataFrame
    data = pd.DataFrame(data, columns=['timestamp', 'temperature', 'relative_humidity', 'time_created'])
    is_duplicate = data.duplicated('timestamp', keep='first') # find duplicated timestamps, keeping only latest forecast
    data = data[~is_duplicate]
    data = data.sort_values('timestamp', axis=0, ascending=True) # sort in ascending order of timestamp (i.e. forecasted time)
    data = data.drop('time_created', axis=1) # remove time_created column
    # the following is done to ensure that the output of this function is in the same format
    # as the output of `getDaysWeather`
    timestamp = data['timestamp'].dt.to_pydatetime() # convert timestamp to python datetime
    temperature = data["temperature"].to_numpy()
    relative_humidity = data["relative_humidity"].to_numpy()
    data = np.vstack([timestamp, temperature, relative_humidity]) # concatenate into a matrix
    data = data.transpose()
    data = data.tolist() # convert numpy array to list of lists
    data = list(map(tuple, data)) # convert list of lists to list of tuples
    return data


def getDaysHumidityTemp(deltaDays=10, numRows=5, sensorID=27):
    # select * from aranet_trh_data where sensor_id=27 order by timestamp desc limit 10;
    today = datetime.datetime.now()
    delta = datetime.timedelta(days=deltaDays)
    dateNumDaysAgo = today - delta
    params = {
        "sensor_id": sensorID,
        "timestamp": dateNumDaysAgo.strftime("%Y-%m-%d %H:%M:%S"),
        "numRows": numRows,
    }

    humidity_transaction_template = """
  select
    timestamp, temperature, humidity
  from
    aranet_trh_data
  where (sensor_id = {{ sensor_id }} AND timestamp >= {{ timestamp }})
  order by
    timestamp asc
  limit {{ numRows }}
  """
    j = JinjaSql(param_style="pyformat")
    query, bind_params = j.prepare_query(humidity_transaction_template, params)
    return getData(get_sql_from_template(query=query, bind_params=bind_params))


def getDaysHumidity(deltaDays=10, numRows=5, sensorID=27):
    # select * from aranet_trh_data where sensor_id=27 order by timestamp desc limit 10;
    today = datetime.datetime.now()
    delta = datetime.timedelta(days=deltaDays)
    dateNumDaysAgo = today - delta
    params = {
        "sensor_id": sensorID,
        "timestamp": dateNumDaysAgo.strftime("%Y-%m-%d %H:%M:%S"),
        "numRows": numRows,
    }

    humidity_transaction_template = """
  select
    timestamp, humidity
  from
    aranet_trh_data
  where (sensor_id = {{ sensor_id }} AND timestamp >= {{ timestamp }})
  order by
    timestamp asc
  limit {{ numRows }}
  """
    j = JinjaSql(param_style="pyformat")
    query, bind_params = j.prepare_query(humidity_transaction_template, params)
    return getData(get_sql_from_template(query=query, bind_params=bind_params))


def insert_particles(particles_array):
    insertQuery = "INSERT INTO model_parameter(parameter_id, parameter_index, parameter_value) VALUES (%s,%s,%s)"
    conn = None
    try:
        conn = openConnection()
        if conn is not None:
            cur = conn.cursor()
            cur.executemany(insertQuery, particles_array)
            conn.commit()
            cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(error)
    finally:
        closeConnection(conn=conn)


def getDataPointHumidity(sensorID=27, numRows=1):
    # select * from aranet_trh_data where sensor_id=27 order by timestamp desc limit 10;
    params = {"sensor_id": sensorID, "num_Rows": numRows}

    humidity_transaction_template = """
  select
    timestamp, humidity
  from
    aranet_trh_data
  where (sensor_id = {{ sensor_id }})
  order by
    timestamp desc
  limit {{ num_Rows }}
  """
    j = JinjaSql(param_style="pyformat")
    query, bind_params = j.prepare_query(humidity_transaction_template, params)
    return getData(get_sql_from_template(query=query, bind_params=bind_params))


def getDataPoint(filepath=None):
    if filepath:
        LastDataPoint = pd.read_csv(filepath)
        jj = np.size(LastDataPoint, 1)
        if jj > 1:
            DataPoint = float(LastDataPoint[str(jj)])
        else:
            DataPoint = 0.5  # dummy value
        return DataPoint
    else:
        dp_database = np.asarray(getDataPointHumidity())[0, 1]
        return dp_database


def testEnergy():
    sql_command = "SELECT * FROM utc_energy_data WHERE utc_energy_data.timestamp >= '2021-03-12 16:03:11' AND utc_energy_data.timestamp < '2021-09-28 17:03:11'"
    return getData(sql_command)


def insertRow(query, parameters):
    conn = None
    new_row_id = None
    try:
        conn = openConnection()
        if conn is not None:
            # create a cursor
            cur = conn.cursor()
            cur.execute(query, parameters)
            new_row_id = cur.fetchone()[0]
            conn.commit()
            # close the communication with the PostgreSQL
            cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(error)
    finally:
        closeConnection(conn=conn)
        return new_row_id


def insertRows(query, parameters):
    conn = None
    new_row_ids = []
    try:
        conn = openConnection()
        if conn is not None:
            cur = conn.cursor()
            execute_values(cur, query, parameters)
            conn.commit()
            new_row_ids = cur.fetchall()
            cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(error)
    finally:
        closeConnection(conn=conn)
        return len(new_row_ids)



def insertModelRun(sensor_id=None, model_id=None, time_forecast=None):
    if sensor_id is not None:
        if model_id is not None:
            if time_forecast is not None:
                parameters = (sensor_id, model_id, time_forecast)
                sql = """INSERT INTO model_run(sensor_id, model_id, time_forecast)
        VALUES (%s,%s,%s) RETURNING id;"""
                return insertRow(sql, parameters)
    return None


def insertModelProduct(run_id=None, measure_id=None):
    if run_id is not None:
        if measure_id is not None:
            sql = """INSERT INTO model_product(run_id, measure_id)
            VALUES (%s,%s) RETURNING id;"""
            product_id = insertRow(sql, (run_id, measure_id))
            logging.info("Product inserted, logged as ID: {0}".format(product_id))
            return product_id
    return None


def insertModelPrediction(parameters=None):
    num_rows_inserted = 0
    if parameters is not None:
        if len(parameters) > 0:
            sql = """INSERT INTO model_value(product_id,prediction_value, prediction_index)
        VALUES %s RETURNING id"""
            num_rows_inserted = insertRows(sql, parameters)
            return num_rows_inserted
    return num_rows_inserted



# if __name__ == '__main__':
# testInsert()
# particles_array = [(2, 1, 0.4594613726254301), (2, 2, 0.763604572422916), (2, 3, 0.7340651592924317), (2, 0.7047730309779485), (2, 0.4595117250921914)]
# insert_particles(particles_array)
# compareHumiditySources()
# compareDataPoint()
# getDaysWeather(numDays=7, numRows=10)
# humidityDataList = getDaysHumidity(deltaDays=1, numRows=1000)
# # for row in humidityList:
#   # logging.info(row)
# dp = getDataPointHumidity()
# humidityList = []
# # temperature = []
# for row in humidityDataList:
#     humidityList.append(row[1])
#     logging.info(row[1])
#     logging.info(row[0])

# humidity = pd.Series(humidityList)
# # take average and turn to hourly data
# DT = humidityDataList[len(humidityDataList)-1][0]
# logging.info(DT)

# energy = testEnergy()
# logging.info(energy[0])
