# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from typing import Dict
# from functions_scenarioV1 import derivatives, sat_conc
import functions_scenarioV1 as functions_scenario
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pandas import DataFrame
from dataAccess import getDaysHumidityTemp, getDaysWeather, getData, get_sql_from_template
from jinjasql import JinjaSql
import datetime
import os

USE_LIVE = True
filepath_weather = os.path.join(os.path.dirname(__file__),'ExternalWeather.csv')

def setTimeParameters(h2:int=240, numDays:int=10) -> Dict:
  # Start hour h2 is for test only - in live version will be current time
  # h2 = 240
  h1:int = h2-240 # select previous 10 days
  ndp:int = int((h2-h1)/12) # number of data points used for calibration
  timeParameters:Dict = {
    "h2": h2,
    "h1":h1, # select previous 10 days
    "ndp": ndp, # number of data points used for calibration
    "numDays":numDays
  }
  print(timeParameters)
  return timeParameters

def setACHParameters(ACH_OUT_PATH:str,
  ndp:int=10)->Dict:
  ACHinp:np.ndarray = np.genfromtxt(ACH_OUT_PATH, delimiter=',')
  ACHcal = ACHinp[1:,-1*ndp:]*9+1 # selects ACH values corresponding to the last ndp data points
  ACHmean = np.mean(ACHcal,0)
  ACHuq = np.quantile(ACHcal,0.95,0)
  ACHlq = np.quantile(ACHcal,0.05,0)
  ACHParameters:Dict = {
    "ACHcal":ACHcal,
    "ACHmean":ACHmean,
    "ACHuq":ACHuq,
    "ACHlq":ACHlq
  } 
  return ACHParameters
  
def setIASParameters(IAS_OUT_PATH:str,
  ndp:int=10) -> Dict:
  IASinp:np.ndarray = np.genfromtxt(IAS_OUT_PATH, delimiter=',')
  IAScal:float = IASinp[1:,-1*ndp:]*0.75+0.1
  IASmean:float = np.mean(IAScal,0)
  IASuq:float = np.quantile(IAScal,0.95,0)
  IASlq:float = np.quantile(IAScal,0.05,0)
  IASParameters:Dict = {
    'IAScal': IASinp[1:,-1*ndp:]*0.75+0.1,
    'IASmean': IASmean,
    'IASuq': IASuq,
    'IASlq': IASlq
  }
  return IASParameters

# # Set up parameters for runs: 1) BAU mean, 2) Scenario, 3) BAU UQ, 4) BAU LQ
# # Scenario values N, ndh and lshift will come from sliders on dashboard
def setModel(ndp:int=10,
  ach_parameters:Dict={},
  ias_parameters:Dict={}) -> np.ndarray:

  test:np.ndarray = np.zeros((ndp,4,4))
  
  test[:,0,0] = ach_parameters['ACHmean']
  test[:,1,0] = ias_parameters['IASmean']
  test[:,2,0] = 1
  test[:,3,0] = 0

  test[:,0,1] = ach_parameters['ACHmean']
  test[:,1,1] = ias_parameters['IASmean']
  test[:,2,1] = 1
  test[:,3,1] = 0

  test[:,0,2] = ach_parameters['ACHuq']
  test[:,1,2] = ias_parameters['IASlq']
  test[:,2,2] = 1
  test[:,3,2] = 0

  test[:,0,3] = ach_parameters['ACHlq']
  test[:,1,3] = ias_parameters['IASuq']
  test[:,2,3] = 1
  test[:,3,3] = 0

  return test

def setScenario(ventilation_rate:int=1,
  num_dehumidifiers:int=2,
  shift_lighting:int=-3,
  ach_parameters:Dict={},
  ias_parameters:Dict={}) -> np.ndarray:

  # # Scenario 1 - vary ACH
  ScenEval:np.ndarray = np.zeros((8,4,4))
  ScenEval[:,0,0] = ach_parameters['ACHmean'][-1]
  ScenEval[:,0,1] = ventilation_rate
  ScenEval[:,0,2] = ach_parameters['ACHuq'][-1]
  ScenEval[:,0,3] = ach_parameters['ACHlq'][-1]

  ScenEval[:,1,0] = ias_parameters['IASmean'][-1]
  ScenEval[:,1,1] = ias_parameters['IASmean'][-1]
  ScenEval[:,1,2] = ias_parameters['IASlq'][-1]
  ScenEval[:,1,3] = ias_parameters['IASuq'][-1]

  # # Scenario 2 - vary number of dehumidifiers 
  ScenEval[:,2,0] = 1
  ScenEval[:,2,1] = int(num_dehumidifiers/2) # ndh input from slider (integer) (/2 as half farm modelled)
  ScenEval[:,2,2] = 1
  ScenEval[:,2,3] = 1

  # Scenario 3 - shift lighting schedule (+/-hours)
  ScenEval[:,3,0] = 1
  ScenEval[:,3,1] = shift_lighting 
  ScenEval[:,3,2] = 1
  ScenEval[:,3,3] = 1

  return ScenEval

## Run model, using time varying ACH, IAS corresponding to outputs from calibration for 
#  first 10 days, then scenario evaluation values for last 3 days
def runModel(time_parameters:Dict,
  filepath_weather=None,
  params:np.ndarray=[]) -> Dict: 

  results = functions_scenario.derivatives(time_parameters['h1'], 
    time_parameters['h2'], 
    time_parameters['numDays'], 
    params, 
    time_parameters['ndp'],
    filePathWeather=filepath_weather) # runs GES model over ACH,IAS pairs
  T_air = results[1,:,:]
  Cw_air = results[11,:,:]
  RH_air = Cw_air/functions_scenario.sat_conc(T_air)
  results_to_store = {
    'T_air': T_air,
    'RH_air': RH_air  
  }
  print("T_air: {0} RH_air: {1}".format(T_air, RH_air))
  return results_to_store

if __name__ == '__main__':   
  # Get calibrated parameters output from calibration model
  # Stored in database? Currently output to csv file
  ACH_OUT_PATH:str = os.path.join(os.path.dirname(__file__),'ACH_out.csv')
  IAS_OUT_PATH:str = os.path.join(os.path.dirname(__file__),'IAS_out.csv')
  h2:int = 240
  numDays:int = 10

  time_parameters:Dict = setTimeParameters(h2=h2, numDays=numDays)
  ach_parameters = setACHParameters(ACH_OUT_PATH=ACH_OUT_PATH, 
    ndp=time_parameters['ndp'])
  ias_parameters:Dict = setIASParameters(IAS_OUT_PATH=IAS_OUT_PATH,
    ndp=time_parameters['ndp']
  )

  ventilation_rate:int=1
  num_dehumidifiers:int=2
  shift_lighting:int=-3

  model:np.ndarray = setModel(time_parameters['ndp'], 
    ach_parameters=ach_parameters,
    ias_parameters=ias_parameters)

  scenario:np.ndarray = setScenario(ventilation_rate=ventilation_rate,
    num_dehumidifiers = num_dehumidifiers,
    shift_lighting = shift_lighting,
    ach_parameters=ach_parameters,
    ias_parameters=ias_parameters)

  params:np.ndarray = np.concatenate((model, scenario)) # put scenario on the end of the calibrated parameters
  
  results = runModel(time_parameters=time_parameters,
    filepath_weather= None if USE_LIVE else filepath_weather,
    params=params)
  
  T_air = results['T_air']
  RH_air = results['RH_air']

    ## Plot Results
  ExternalWeather = np.asarray(getDaysWeather(numDays+1, numRows=(numDays+1)*24))

  ind = h2-time_parameters['h1']+1

  TWeather= ExternalWeather[-ind:,1].astype(np.float64) # +1 to ensure correct end point
  RHWeather = ExternalWeather[-ind:,2].astype(np.float64)


  # Internal conditions

  MidFarmRH2_ID = 27
  deltaDays = 11
  sensorID=MidFarmRH2_ID
  numRows = deltaDays*24*6
  today = datetime.datetime.now()
  delta = datetime.timedelta(days=deltaDays)
  dateNumDaysAgo = today - delta

  params = {'sensor_id':sensorID,
    'timestamp':dateNumDaysAgo.strftime("%Y-%m-%d %H:%M:%S"), 
    'numRows':numRows}

  humidity_transaction_template = '''
    select
      timestamp, humidity, temperature
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

  test = getData(get_sql_from_template(query=query, bind_params=bind_params))

  idx = [x[0] for x in test]
  val1 = [x[1] for x in test]
  val2 = [x[2] for x in test]

  RH_10_minutes = pd.Series(val1, index=idx)
  T_10_minutes = pd.Series(val2, index=idx)

  RHData = RH_10_minutes.resample('H').mean()
  TData = T_10_minutes.resample('H').mean()

  #

  p1 = time_parameters['h1'] # start hour 
  delta_h = 12 # hours between data points
  p2 = time_parameters['ndp']*delta_h+p1 # end data point 

  sq = np.linspace(p1,p2,time_parameters['ndp']+1,endpoint='true')
  seq = sq.astype(np.int64)

  #date_cols = ["DateTimex"]
  #Data = pd.read_csv("TRHE2018.csv", parse_dates=date_cols)
  #RHData =Data['MidFarmRH2']
  #TData =Data['MidFarmT']
      
  #t = np.linspace(h1,h2+3*24,1+240+3*24)
  t = np.linspace(time_parameters['h1']-h2,3*24,1+240+3*24)
  t1 = np.linspace(0,3*24,1+3*24)
  td = np.linspace(time_parameters['h1']-h2,0,21)

  dpRH = RHData[seq]
  dpT = TData[seq]+273.15
  dpCw = dpRH/100 * functions_scenario.sat_conc(dpT)

  fig = plt.figure()

  ax1 = fig.add_subplot(1,2,1)
  plt.plot(t,T_air[:,0]-273.15,'r')
  #p1 = plt.plot(t,T_air[:,2]-273.15,'r:')
  #p2 = plt.plot(t,T_air[:,3]-273.15,'r:')
  ax1.fill_between(t[:-73], T_air[:-73,2]-273.15, T_air[:-73,3]-273.15, color='red', alpha = 0.2)
  #plt.plot(t,T_air[:,1],'b--')
  plt.plot(t1,T_air[-73:,1]-273.15,'b--')
  plt.scatter(td,dpT-273.15, marker='.', color='k')
  plt.xticks(fontsize=8)
  plt.yticks(fontsize=8)
  ax1.set_xlabel('Hour', fontsize=8)
  ax1.set_ylabel('Temperature ($\mathregular{^{o}}$C)', fontsize=8)
  ax1.set_title('Temperature', fontsize=10)
  ax1.axvline(x=0, color='k')
  ax1.set_xlim(-120, 72)

  ax3 = fig.add_subplot(1,2,2)
  lbl1 = str(int(ventilation_rate)) + ' ACH'
  lbl2 = ', ' + str(int(num_dehumidifiers)) + ' DH'
  lbl3 = ', ' + str(int(shift_lighting)) + ' hours'
  plt.plot(t,100*RH_air[:,0],'r', label='BAU')
  ax3.fill_between(t[:-73], 100*RH_air[:-73,2], 100*RH_air[:-73,3], color='red', alpha = 0.2)

  #plt.plot(t,100*RH_air[:,1],'b--', label='Max N')
  plt.plot(t1,100*RH_air[-73:,1],'b--', label= lbl1 + lbl2 + lbl3)
  plt.scatter(td,dpRH, marker='.', color='k', label='Data')
  ax3.set_title('Relative Humidity', fontsize=10)
  plt.xticks(fontsize=8)
  plt.yticks(fontsize=8)
  ax3.set_xlabel('Hour', fontsize=8)
  ax3.set_ylabel('Relative Humidity (%)', fontsize=8)
  ax3.legend(loc='best', fontsize='small')
  ax3.axvline(x=0, color='k')
  ax3.set_xlim(-120, 72)


  plt.subplots_adjust(wspace=0.5)

  # Calculate statistics and produce pie charts. Note need too cold as well? Check
  # setpoints with Mel

  setTmax = 25 + 273.15
  setTmin = 20 + 273.15
  setRHmax = 0.85
  setRHmin = 0.5

  TBAUstat = T_air[-73:,0]
  TSEstat = T_air[-73:,1]

  RHBAUstat = RH_air[-73:,0]
  RHSEstat = RH_air[-73:,1]

  testTBAU = TBAUstat>setTmax
  testTBAU_low = TBAUstat<setTmin
  testTSE = TSEstat>setTmax
  testTSE_low = TSEstat<setTmin

  testRHBAU = RHBAUstat>setRHmax
  testRHBAU_low = RHBAUstat<setRHmin
  testRHSE = RHSEstat>setRHmax
  testRHSE_low = RHSEstat<setRHmin

  #y1 = ([np.sum(testTBAU), 72])
  y1 = {'T<Tmin': np.sum(testTBAU_low), 'T OK': 72-np.sum(testTBAU)-np.sum(testTBAU_low), 'T>Tset': np.sum(testTBAU)}
  names1 = [key for key,value in y1.items() if value!=0]
  values1 = [value for value in y1.values() if value!=0]

  #y2 = ([np.sum(testTSE), 72])
  #y2 = {'T<Tset': 72-np.sum(testTSE), 'T>Tset': np.sum(testTSE)}
  y2 = {'T<Tmin': np.sum(testTSE_low), 'T OK': 72-np.sum(testTSE)-np.sum(testTSE_low), 'T>Tset': np.sum(testTSE)}
  names2 = [key for key,value in y2.items() if value!=0]
  values2 = [value for value in y2.values() if value!=0]

  #y3 = ([np.sum(testRHBAU), 72])
  #y3 = {'RH<RHset': 72-np.sum(testRHBAU), 'RH>RHset': np.sum(testRHBAU)}
  y3 = {'RH<RHmin': np.sum(testRHBAU_low), 'RH OK': 72-np.sum(testRHBAU)-np.sum(testRHBAU_low), 'RH>RHset': np.sum(testRHBAU)}
  names3 = [key for key,value in y3.items()]
  values3 = [value for value in y3.values()]

  #y4 = ([np.sum(testRHSE), 72])
  #y4 = {'RH<RHset': 72-np.sum(testRHSE), 'RH>RHset': np.sum(testRHSE)}
  y4 = {'RH<RHmin': np.sum(testRHSE_low), 'RH OK': 72-np.sum(testRHSE)-np.sum(testRHSE_low), 'RH>RHset': np.sum(testRHSE)}
  names4 = [key for key,value in y4.items()]
  values4 = [value for value in y4.values()]

  fig2 = plt.figure()

  #Tlabels = ['T>Tset', 'T<Tset']
  #RHlabels = ['RH>RHset', 'RH<RHset']

  ax11 = fig2.add_subplot(2,2,1)

  plt.pie(values1, colors = ['blue','green','red'], startangle = 90, labels = names1, textprops={'fontsize': 8}) 
  ax11.set_title('Temperature - BAU', fontsize = 8) 
  
  ax12 = fig2.add_subplot(2,2,3)   
  
  plt.pie(values2, colors = ['blue','green','red'], startangle = 90, labels = names2, textprops={'fontsize': 8})
  ax12.set_title('Temperature - Scenario', fontsize = 8) 

  ax31 = fig2.add_subplot(2,2,2)

  plt.pie(values3, colors = ['blue','green','red'], startangle = 90, labels = names3, textprops={'fontsize': 8})  
  ax31.set_title('RH - BAU', fontsize = 8) 
  
  ax32 = fig2.add_subplot(2,2,4)   
  
  plt.pie(values4, colors = ['blue','green','red'], startangle = 90, labels = names4, textprops={'fontsize': 8})
  ax32.set_title('RH - Scenario', fontsize = 8) 

  
  

