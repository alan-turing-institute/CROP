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
from dataAccess import getDaysWeather, getDaysHumidity, getData, get_sql_from_template
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
  return timeParameters

def setACHParameters(ACH_OUT_PATH:str,
  ndp:int=10) -> Dict:
  ACHinp:np.ndarray = np.genfromtxt(ACH_OUT_PATH, delimiter=',')
  ACHcal:float = ACHinp[1:,-1*ndp:]*9+1, # selects ACH values corresponding to the last ndp data points
  ACHmean:float = np.mean(ACHcal,0)
  ACHuq:float= np.quantile(ACHcal,0.95,0)
  ACHlq:float= np.quantile(ACHcal,0.05,0)
  ACHParameters:Dict = {
    "ACHcal":ACHcal,
    "ACHmean":ACHmean,
    "ACHuq":ACHuq,
    "ACHlq":ACHlq
  } 
  print(ACHParameters['ACHmean'])
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
  params:np.ndarray=[]) -> None: 

  results = functions_scenario.derivatives(time_parameters['h1'], 
    time_parameters['h2'], 
    time_parameters['numDays'], 
    params, 
    time_parameters['ndp'],
    filePathWeather=filepath_weather) # runs GES model over ACH,IAS pairs

  T_air = results[1,:,:]
  Cw_air = results[11,:,:]
  RH_air = Cw_air/functions_scenario.sat_conc(T_air)
  
  print("T_air: {0} RH_air: {1}".format(T_air, RH_air))

if __name__ == '__main__':

  # Get calibrated parameters output from calibration model
  # Stored in database? Currently output to csv file
  ACH_OUT_PATH:str = os.path.join(os.path.dirname(__file__),'ACH_out.csv')
  IAS_OUT_PATH:str = os.path.join(os.path.dirname(__file__),'IAS_out.csv')
  h2:int = 240
  numDays:int = 10

  time_parameters:Dict = setTimeParameters(h2=h2, numDays=numDays)
  ach_parameters:Dict = setACHParameters(ACH_OUT_PATH=ACH_OUT_PATH, 
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
  
  runModel(time_parameters=time_parameters,
    filepath_weather= None if USE_LIVE else filepath_weather,
    params=params)
  

