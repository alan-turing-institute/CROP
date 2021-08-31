from dataAccess import getDaysWeather, getDaysHumidity
import numpy as np
import pandas as pd

def compareWeather():
  temperatureIndex = 1
  humidityIndex = 2
  temperatureList = []
  humidityList = []
  weatherSQL = getDaysWeather()
  for row in weatherSQL:
    temperatureList.append(row[temperatureIndex])
    humidityList.append(row[humidityIndex])
  temperatureList = np.array(temperatureList)
  humidityList = np.array(humidityList)
  print(temperatureList)
  
  '''
  timestamp, temperature, relative_humidity
  31/12/2018 17:00,9.7,74
  '''
  filepath_weather = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/ExternalWeather_subset.csv'
  weatherCSV = np.genfromtxt(filepath_weather, delimiter=',')
  print(weatherCSV[:, temperatureIndex])

def compareSensor():
  filepath_TRHE = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/TRHE2018_subset.csv'
  date_cols = ["DateTimex"]
  sensorCSV = pd.read_csv(filepath_TRHE, parse_dates=date_cols)
  RHDataCSV =sensorCSV['MidFarmRH2']
  print (type(sensorCSV))
  print (RHDataCSV)

  sensorSQL = pd.DataFrame(getDaysHumidity(),columns=['DateTimex','MidFarmT','MidFarmRH2'])
  RHDataSQL =sensorSQL['MidFarmRH2']
  print (type(sensorSQL))
  print (RHDataSQL)

def compareDataPoint():
  filepath_datapoint = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/DataPoint.csv'
  LastDataPoint = pd.read_csv(filepath_datapoint)
  jj = np.size(LastDataPoint,1)
  DataPoint = 0.5 # dummy value
  if jj > 1:
    DataPoint = float(LastDataPoint[str(jj)])
  print(DataPoint)

if __name__ == '__main__':
    # connect()
  filepath_datapoint = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/DataPoint.csv'
  LastDataPoint = pd.read_csv(filepath_datapoint)
  jj = np.size(LastDataPoint,1)

  if jj > 1:
    DataPoint = float(LastDataPoint[str(jj)])
  else:
    DataPoint = 0.5 # dummy value
  
  print (jj)
  print (DataPoint)


  
  

  