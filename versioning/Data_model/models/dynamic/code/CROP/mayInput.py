from dataAccess import getDaysWeather, getDaysHumidity, insert_particles
import numpy as np
import pandas as pd
import os

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

def assembleParticlesHistory():
  PARAMETER_ID_ACH = 2
  PARAMETER_ID_IAS = 3
  filepath_ach = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/ACH_v2_out.csv' 
  filepath_ias = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/IAS_v2_out.csv' 
  df_ACH = pd.read_csv(filepath_ach)
  insertParticlesHistory(PARAMETER_ID_ACH, df_ACH)
  df_IAS = pd.read_csv(filepath_ias)
  insertParticlesHistory(PARAMETER_ID_IAS, df_IAS)
  
def insertParticlesHistory(particle_id, particle_df):
  particle_history_step = particle_df.columns
  for col in range(len(particle_history_step)-20, len(particle_history_step)):
    ach = particle_df.iloc[:,col]
    ach_array = []
    for p in range(len(ach)):
      ach_tuple = (particle_id, p, ach[p])
      ach_array.append(ach_tuple)
    
    print("ParticleID:{0} History:{1}".format(particle_id, col))
    insert_particles(ach_array)

if __name__ == '__main__':
  # assembleParticlesHistory()
  filepath_ACH = os.path.join(os.path.dirname(__file__),os.path.pardir, os.pardir,"data","ACH_out.csv")
  df_ACH = pd.read_csv(filepath_ACH)
  print(df_ACH.tail(1))
  
  
  # for row in range(len(df_ACH)):
  #   for col in range(1,len(ACH_columns)):
  #     particleIndex = particleIndex+1
  #     particleValue = df_ACH.loc[row,ACH_columns[col]]
  #     # print("[{0},{1}] = {2}".format(row, col, df_ACH.loc[row,ACH_columns[col]]))
  #     ACH_array.append((particleIndex, particleValue))
  # insert_particles(ACH_array)
