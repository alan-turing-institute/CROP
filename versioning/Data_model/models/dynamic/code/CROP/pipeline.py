# from CalibrationV2 import LatestTime
from TestScenarioV2 import testScenario
from CalibrationV2 import runCalibration, FILEPATH_WEATHER_LOW_12
import pandas as pd
from dataAccess import (deleteResults, 
  insertModelRun, 
  insertModelProduct, 
  insertModelPrediction)

MODEL_GES_ID = 3
SENSOR_RH_16B2_ID = 27

MEASURE_MEAN_TEMPERATURE = {'measure_id':1, 'result_index':0}
MEASURE_SCENARIO_TEMPERATURE = {'measure_id':9, 'result_index':1}
MEASURE_UPPER_TEMPERATURE = {'measure_id':2, 'result_index':3}
MEASURE_LOWER_TEMPERATURE = {'measure_id':3, 'result_index':2}

MEASURE_MEAN_HUMIDITY = {'measure_id':10, 'result_index':0}
MEASURE_SCENARIO_HUMIDITY = {'measure_id':11, 'result_index':1}
MEASURE_LOWER_HUMIDITY = {'measure_id':12, 'result_index':2}
MEASURE_UPPER_HUMIDITY = {'measure_id':13, 'result_index':3}

def assemble_temperature_values(product_id, result_index, T_air):
  def to_celcius(temp_kelvin):
    return (temp_kelvin-273.15)   
  prediction_parameters = []
  for prediction_index, hr in enumerate(T_air):
    prediction_parameters.append((product_id, to_celcius(hr[result_index]), prediction_index))
  return prediction_parameters

if __name__ == '__main__':

  measures_temperature = [MEASURE_MEAN_TEMPERATURE,
  MEASURE_SCENARIO_TEMPERATURE] 
  # MEASURE_LOWER_TEMPERATURE,
  # MEASURE_UPPER_TEMPERATURE]

  measures_humidity = []

  # results = testScenario()
  T_air=[[294.95083093, 294.95083093, 294.04751092, 295.95938605],
  [294.36003495, 294.36003495, 293.40987372, 295.50316643],
  [294.17041032, 294.17041032, 293.23090581, 295.33660461]]

  deleteResults()
  df_weather = pd.read_csv(FILEPATH_WEATHER_LOW_12, 
    header=None, 
    names=['Timestamp','Temperature','Humidity'])
  forecast_date = pd.to_datetime(df_weather.tail(1)['Timestamp'].item())
  print("Forecast Date: {0}".format(forecast_date))
  
  run_id = insertModelRun(sensor_id=SENSOR_RH_16B2_ID,
    model_id=MODEL_GES_ID,
    time_forecast=forecast_date)

  if run_id is not None:
    print("Run inserted, logged as ID: {0}".format(run_id))
    for measure in measures_temperature:
      product_id = insertModelProduct(run_id=run_id, 
        measure_id=measure['measure_id'])
      value_parameters = assemble_temperature_values(product_id=product_id, 
        result_index=measure['result_index'],
        T_air=T_air)
      print(value_parameters)
      num_rows_inserted = insertModelPrediction(value_parameters)
      print("{0} rows inserted".format(num_rows_inserted))
  
    
  
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
  #   for measure in measures_temperature:
  #   measures = [MEASURE_TEMPERATURE, MEASURE_HUMIDITY]
  #   insertModelProducts(run_id=run_id, measures=measures)
    
  
  
  
  
