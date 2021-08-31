from jinjasql.core import bind
from config import config
import psycopg2
import datetime
from jinjasql import JinjaSql
from six import string_types
from copy import deepcopy


def openConnection():
  """ Connect to the PostgreSQL database server """
  conn = None
  try:
    # read connection parameters
    params = config()

    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect(**params)

  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
  finally:
    return conn

def closeConnection(conn):
  if (conn is not None):
    conn.close()
    print('Database connection closed.')

def connect():
  """ Connect to the PostgreSQL database server """
  conn = None
  try:
    conn = openConnection()
    if (conn is not None):
      # create a cursor
      cur = conn.cursor()
      cur.execute('SELECT version()')
      db_version = cur.fetchone()

      # execute a statement
      print('PostgreSQL database version:{0}'.format(db_version))
      
      # close the communication with the PostgreSQL
      cur.close()
  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
  finally:
    closeConnection(conn=conn)

def printRowsHead(rows, numrows=5):
  print('Printing:{0} of {1}'.format(numrows, len(rows) ))
  for row in rows[:numrows]:
    print(row)

def deleteData(query):
  conn = None
  try:
    conn = openConnection()
    if (conn is not None):
      cur = conn.cursor()
      cur.execute(query)
      conn.commit()
      cur.close()
  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
  finally:
    closeConnection(conn=conn)

def getData(query):
  conn = None
  try:
    conn = openConnection()
    if (conn is not None):
      # create a cursor
      cur = conn.cursor()
      cur.execute(query)
      rows = cur.fetchall()
      printRowsHead(rows)
      
      # close the communication with the PostgreSQL
      cur.close()
  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
  finally:
    closeConnection(conn=conn)
    return rows

def quote_sql_string(value):
  '''
  If `value` is a string type, escapes single quotes in the string
  and returns the string enclosed in single quotes.
  '''
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
  params = {'timestamp':dateNumDaysAgo.strftime("%Y-%m-%d %H:%M:%S"), 'numRows':numRows}

  weather_transaction_template = '''
  select
    timestamp, temperature, relative_humidity
  from 
    iweather 
  where timestamp >= {{ timestamp }}
  order by 
    timestamp asc 
  limit {{ numRows }}
  '''
  j = JinjaSql(param_style='pyformat')
  query, bind_params = j.prepare_query(weather_transaction_template, params)
  # print(get_sql_from_template(query=query, bind_params=bind_params))
  return getData(get_sql_from_template(query=query, bind_params=bind_params))

def getDaysHumidity(numDays=5, numRows=5):
  # select * from zensie_trh_data where sensor_id=27 order by timestamp desc limit 10;
  today = datetime.datetime.now()
  delta = datetime.timedelta(days=numDays)
  dateNumDaysAgo = today - delta
  params = {'sensor_id':27,
  'timestamp':dateNumDaysAgo.strftime("%Y-%m-%d %H:%M:%S"), 
  'numRows':numRows}

  humidity_transaction_template = '''
  select
    timestamp, temperature, humidity
  from 
    zensie_trh_data 
  where (sensor_id = {{ sensor_id }} AND timestamp >= {{ timestamp }})
  order by 
    timestamp asc 
  limit {{ numRows }}
  '''
  j = JinjaSql(param_style='pyformat')
  query, bind_params = j.prepare_query(humidity_transaction_template, params)
  print(get_sql_from_template(query=query, bind_params=bind_params))
  return getData(get_sql_from_template(query=query, bind_params=bind_params))

if __name__ == '__main__':
    # connect()
  # getDaysWeather()
  # getHumidity()