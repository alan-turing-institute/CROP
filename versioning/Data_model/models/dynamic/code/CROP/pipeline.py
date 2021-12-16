# from CalibrationV2 import LatestTime
from TestScenarioV2 import testScenario
from CalibrationV2 import runCalibration, FILEPATH_WEATHER_LOW_12
import pandas as pd
from dataAccess import deleteResults, insertModelRun, insertModelProducts

if __name__ == '__main__':
  MODEL_GES_ID = 3
  SENSOR_RH_16B2_ID = 27
  MEASURE_MEAN_TEMPERATURE = 1
  MEASURE_UPPER_TEMPERATURE = 2
  MEASURE_LOWER_TEMPERATURE = 3
  MEASURE_SCENARIO_TEMPERATURE = 9
  MEASURE_MEAN_HUMIDITY = 10
  MEASURE_SCENARIO_HUMIDITY = 11
  MEASURE_LOWER_HUMIDITY = 12
  MEASURE_UPPER_HUMIDITY = 13

  measures_temperature = [MEASURE_MEAN_TEMPERATURE,
  MEASURE_SCENARIO_TEMPERATURE, 
  MEASURE_LOWER_TEMPERATURE,
  MEASURE_UPPER_TEMPERATURE]

  # results = testScenario()
  T_air=[[294.95083093, 294.95083093, 294.04751092, 295.95938605],
 [294.36003495, 294.36003495, 293.40987372, 295.50316643],
 [294.17041032, 294.17041032, 293.23090581, 295.33660461]]
  T_air_celcius = []
  
#   RH_air = [[0.62324361, 0.62324361, 0.62324361, 0.62324361]
#  [0.60622243, 0.60622243, 0.56561664, 0.66188203]
#  [0.60958018, 0.60958018, 0.57205266, 0.66187175]]

  
  # print(results['RH_air'])
  # deleteResults()
  # df_weather = pd.read_csv(FILEPATH_WEATHER_LOW_12, header=None, names=['Timestamp','Temperature','Humidity'])
  # forecast_date = pd.to_datetime(df_weather.tail(1)['Timestamp'].item())
  # parameters = (SENSOR_RH_16B2_ID, MODEL_GES_ID,forecast_date)
  # print("Forecast Date: {0}".format(forecast_date))
  # run_id = insertModelRun(sensor_id=SENSOR_RH_16B2_ID, model_id=MODEL_GES_ID,time_forecast=forecast_date)
  # if run_id is not None:
  #   print("Run inserted, logged as ID: {0}".format(run_id))
  #   measures = [MEASURE_TEMPERATURE, MEASURE_HUMIDITY]
  #   insertModelProducts(run_id=run_id, measures=measures)
    
  
  
  
  
