from dataAccess import getDaysWeather
import numpy as np

def getWeatherSQL():
  return getDaysWeather()

def getWeatherCSV():
  '''
  timestamp, temperature, relative_humidity
  31/12/2018 17:00,9.7,74
  '''
  filepath_weather = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/ExternalWeather_subset.csv'
  return np.genfromtxt(filepath_weather, delimiter=',')
  
def printRowsHead(rows, numrows=10):
  for row in rows[:numrows]:
    print(row)

def compareWeather():
  temperatureIndex = 1
  humidityIndex = 2
  temperatureList = []
  humidityList = []
  weatherSQL = getWeatherSQL()
  for row in weatherSQL:
    temperatureList.append(row[temperatureIndex])
    humidityList.append(row[humidityIndex])
  temperatureList = np.array(temperatureList)
  humidityList = np.array(humidityList)
  print(np.array(temperatureList))
  
  weatherCSV = getWeatherCSV()
  print(weatherCSV[:, temperatureIndex])

if __name__ == '__main__':
    # connect()
    compareWeather()
  
  
  

  