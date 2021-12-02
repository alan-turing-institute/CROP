# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 15:20:43 2021

@author: rmw61
"""
import datetime
import pandas as pd
from jinjasql import JinjaSql

from dataAccess import getData, get_sql_from_template

MidFarmRH2_ID = 27
deltaDays = 10
sensorID=MidFarmRH2_ID
numRows = deltaDays*24*6

today = datetime.datetime.now()
delta = datetime.timedelta(days=deltaDays)

# Weather
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

Weather = getData(get_sql_from_template(query=query, bind_params=bind_params))

Weather_hour = pd.DataFrame(Weather, columns = ['DateTime','T_e', 'RH_e']).set_index('DateTime')

#test = Weather_10_minutes.resample('H').mean()

# Relative Humidity
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

MonitoredData = getData(get_sql_from_template(query=query, bind_params=bind_params))

Monitored_10_minutes = pd.DataFrame(MonitoredData, columns = ['DateTime','T_i','RH_i']).set_index('DateTime')

Monitored_hour = Monitored_10_minutes.resample('H').mean()


#  Check final timestamps for RH_hour and Weather

print(Monitored_hour[-1:].index == Weather_hour[-1:].index)

# Select oldest of the two final timestamps ( or most recent 3am/3pm time 
# which occurs in both)

LatestTime = min((Monitored_hour[-1:].index).time, (Weather_hour[-1:].index).time)

print(LatestTime)


# Select data for 10 days prior to selected timestamp - boolean mask?




# Check length of arrays


#  If missing data, impute weather data  (method?)


# If missing data, assume no change in RH but fill in missing data points



# Check length of arrays again - should be two arrays of equal length






