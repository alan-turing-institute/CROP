from jinjasql.core import bind
from config import config
import psycopg2
import datetime
from jinjasql import JinjaSql
from six import string_types
from copy import deepcopy
import numpy as np
import pandas as pd


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

def printRowsHead(rows, numrows=0):
  print('Printing:{0} of {1}'.format(numrows, len(rows) ))
  if (numrows == 0):
    for row in rows[:len(rows)]:
      print(row)  
  else:
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
      printRowsHead(rows, numrows=10)
      
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

def getDaysHumidityTemp(deltaDays=10, numRows=5, sensorID=27):
  # select * from zensie_trh_data where sensor_id=27 order by timestamp desc limit 10;
  today = datetime.datetime.now()
  delta = datetime.timedelta(days=deltaDays)
  dateNumDaysAgo = today - delta
  params = {'sensor_id':sensorID,
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
  # print(get_sql_from_template(query=query, bind_params=bind_params))
  return getData(get_sql_from_template(query=query, bind_params=bind_params))

def getDaysHumidity(deltaDays=10, numRows=5, sensorID=27):
  # select * from zensie_trh_data where sensor_id=27 order by timestamp desc limit 10;
  today = datetime.datetime.now()
  delta = datetime.timedelta(days=deltaDays)
  dateNumDaysAgo = today - delta
  params = {'sensor_id':sensorID,
  'timestamp':dateNumDaysAgo.strftime("%Y-%m-%d %H:%M:%S"), 
  'numRows':numRows}

  humidity_transaction_template = '''
  select
    timestamp, humidity
  from 
    zensie_trh_data 
  where (sensor_id = {{ sensor_id }} AND timestamp >= {{ timestamp }})
  order by 
    timestamp asc 
  limit {{ numRows }}
  '''
  j = JinjaSql(param_style='pyformat')
  query, bind_params = j.prepare_query(humidity_transaction_template, params)
  # print(get_sql_from_template(query=query, bind_params=bind_params))
  return getData(get_sql_from_template(query=query, bind_params=bind_params))

def insert_particles(particles_array):
  insertQuery = "INSERT INTO model_parameter(parameter_id, parameter_index, parameter_value) VALUES (%s,%s,%s)"
  conn = None
  try:
    conn = openConnection()
    if (conn is not None):
      cur = conn.cursor()
      cur.executemany(insertQuery, particles_array)
      conn.commit()
      cur.close()
  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
  finally:
    closeConnection(conn=conn)

def getDataPointHumidity(sensorID=27, numRows=1):
  # select * from zensie_trh_data where sensor_id=27 order by timestamp desc limit 10;
  params = {'sensor_id':sensorID, 
    'num_Rows':numRows}

  humidity_transaction_template = '''
  select
    timestamp, humidity
  from 
    zensie_trh_data 
  where (sensor_id = {{ sensor_id }})
  order by 
    timestamp desc 
  limit {{ num_Rows }}
  '''
  j = JinjaSql(param_style='pyformat')
  query, bind_params = j.prepare_query(humidity_transaction_template, params)
  # print(get_sql_from_template(query=query, bind_params=bind_params))
  return getData(get_sql_from_template(query=query, bind_params=bind_params))

def compareWeatherSources():
  database_weather = np.asarray(getDaysWeather())
  filepath_weather = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/ExternalWeather_subset.csv'
  csv_weather = np.genfromtxt(filepath_weather, delimiter=',')
  print ("Example weather database:{0}".format(database_weather[:,1]))
  print ("Example weather csv:{0}".format(csv_weather[1:5,1]))

  print ("Example weather dtype database:{0}".format(type(database_weather[:,1][1])))
  print ("Example weather dtype csv:{0}".format(type(csv_weather[1:5,1][1])))
  
  print (np.isnan(csv_weather[1:5,1]))
  temp = database_weather[1:5,1].astype(np.float64)
  print (np.isnan(temp))

def compareHumiditySources():
  date_cols = ["DateTimex"]
  Data_csv = pd.read_csv("/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/TRHE2018_subset.csv", parse_dates=date_cols)
  RHData_CSV =Data_csv['MidFarmRH2']
  print("CSV Type: {0}".format(type(RHData_CSV)))
  print("CSV Shape: {0}".format(RHData_CSV.shape)) 
  print("CSV: {0}".format(RHData_CSV)) 
  
  MidFarmRH2_ID = 27
  Data_database=getDaysHumidity(numRows=7, sensorID=MidFarmRH2_ID)
  humidity = []
  temperature = []
  for row in Data_database:
    humidity.append(row[1])
    temperature.append(row[0])
  humidity = pd.Series(humidity)
  temperature = pd.Series(temperature)
  print("Db Type: {0}".format(type(humidity)))
  print("Db Shape: {0}".format(humidity.shape))
  print("Db: {0}".format(humidity))

def getDataPoint(filepath=None):
  if (filepath):
    LastDataPoint = pd.read_csv(filepath)
    jj = np.size(LastDataPoint,1)
    if jj > 1:
        DataPoint = float(LastDataPoint[str(jj)])
    else:
        DataPoint = 0.5 # dummy value
    return DataPoint
  else: 
    dp_database = np.asarray(getDataPointHumidity())[0,1]
    return dp_database

def compareDataPoint():
  dp_database = getDataPoint()
  print("Source: Database Type: {0} Value:{1}".format(type(dp_database), dp_database))
  filepath_datapoint = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/DataPoint.csv'
  dp_csv = getDataPoint(filepath_datapoint)
  print("Source: CSV Type: {0} Value:{1}".format(type(dp_csv), dp_csv))

def testEnergy():
  sql_command = "SELECT * FROM utc_energy_data WHERE utc_energy_data.timestamp >= '2021-03-12 16:03:11' AND utc_energy_data.timestamp < '2021-09-28 17:03:11'"
  return getData(sql_command)

if __name__ == '__main__':
  # particles_array = [(2, 1, 0.4594613726254301), (2, 2, 0.763604572422916), (2, 3, 0.7340651592924317), (2, 0.7047730309779485), (2, 0.4595117250921914)]
  # insert_particles(particles_array)
  # compareHumiditySources()
  # compareDataPoint()
  #getDaysWeather(numDays=7, numRows=10)
  humidityDataList = getDaysHumidity(deltaDays=1, numRows=1000)
  # for row in humidityList:
    # print(row)
  dp = getDataPointHumidity()  
  humidityList = []
  # temperature = []
  for row in humidityDataList:
      humidityList.append(row[1])
      print(row[1])
      print(row[0])

  humidity = pd.Series(humidityList)
  # take average and turn to hourly data
  DT = humidityDataList[len(humidityDataList)-1][0] 
  print(DT)

  #energy = testEnergy()
  #print(energy[0])