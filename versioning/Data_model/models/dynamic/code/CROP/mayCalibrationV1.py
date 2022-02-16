# -*- coding: utf-8 -*-
"""
Created on Mon Jun 14 09:32:23 2021

@author: rmw61
"""

from functionsV1 import derivatives, priorPPF, sat_conc
from dataAccess import getDaysWeather, getDaysHumidity
import pandas as pd
import numpy as np
import sys
sys.path.append("/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/code/Inversion")
from inversion import *
import time
import csv

# Code to run the GU physics-based simulation (GES) to predict temperature and relative
# humidity (RH) in the tunnel, then calibrate the parameters ACH (ventilation rate) and
# IAS (internal air speed) using monitored data.
#
# At each data point the GES code runs using the previous 10 days of weather data
# in order to calculate values for relative humidity at the time corresponding to the 
# data point.  The code runs 60 times with different ACH,IAS pairs to generate 60
# values of RH to use as input for the calibration.
#
# The calibration takes as input the 60 simulated values of RH, the 60 ACH,IAS input 
# pairs that generate the simulated RH values and the monitored data point. A GP is 
# fitted to the 60 RH values and input pairs. The particle filter then uses the GP
# to calculate values for each of the particles (1000 ACH,IAS pairs).
#
# This version (v3) runs a single data point at a time (for inclusion in CROP)

filepath_X = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/X.csv'
filepath_weather = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/ExternalWeather.csv'
filepath_TRHE = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/TRHE2018_subset.csv'
filepath_datapoint = '/Users/myong/Documents/workspace/CROP/versioning/Data_model/models/dynamic/data/DataPoint.csv'

# initialize calibration class
sigmaY = 0.5 # std measurement error GASP lambda_e
nugget = 1e-9 # same as mean GASP parameter 1/lambda_en
cal = calibration.calibrate(priorPPF, sigmaY, nugget)

### Time period for calibration
# To be run every 12 hours 3am, 3pm

tic = time.time()

p1 = 243 # start hour to test code - in CROP will be hour at which the code is run 
    
### Calibration runs

# h2 = int(p1)
# h1 = int(p1-48) # to take previous 10 days data

h1 = 1
h2 = 5
useDataBase=True

Parameters = np.genfromtxt(filepath_X, delimiter=',') # ACH,IAS pairs
NP = np.shape(Parameters)[0]
    
# start = time.time()

if useDataBase:
    results = derivatives(h1, h2, Parameters) # runs GES model over ACH,IAS pairs
else: 
    results = derivatives(h1, h2, Parameters, filePathWeather=filepath_weather) # runs GES model over ACH,IAS pairs

print("CSV: {0}".format(results))
print("Database: {0}".format(results))
T_air = results[1,-1,:]
Cw_air = results[11,-1,:]
RH_air = Cw_air/sat_conc(T_air)

# end = time.time()
# print(end - start)


### Select data
### Here using historic data - will be replaced with datapoint from live database

def getHumidity(filepath = None):
    if filepath:
        date_cols = ["DateTimex"]
        Data = pd.read_csv(filepath, parse_dates=date_cols)
        humidity = Data['MidFarmRH2']
        DT = Data['DateTimex']
        return humidity, DT
    else:
        MidFarmRH2_ID = 27
        humidtyList = getDaysHumidity(numRows=7, sensorID=MidFarmRH2_ID)
        humidity = []
        temperature = []
        for row in humidtyList:
            humidity.append(row[1])
            temperature.append(row[0])
        humidity = pd.Series(humidity)
        temperature = pd.Series(temperature)
        return humidity, temperature

if useDataBase:
    RHData, DT = getHumidity()
else:
    RHData, DT = getHumidity(filepath_TRHE)

dp = RHData[h2]
testdp = np.isnan(dp)


    

# # Initialise DataPoint
DataPoint = getDataPoint_CSV(filepath_datapoint)
    
if testdp == False:
    DataPoint = dp/100
else:
    DataPoint = DataPoint # takes previous value if nan recorded

print("DataPoint:{0}".format(DataPoint))

# LastDataPoint[str(jj+1)] = DataPoint 
# LastDataPoint.to_csv("DataPoint.csv", index=False)

# DT = Data['DateTimex']
# print(DT[h2])

# ### Run calibration

# ## Standardise RH_air
    
ym = 0.6456 # values chosen to ensure comparability against MATLAB model
ystd = 0.0675

RH_s = (RH_air - ym)/ystd
print ("Standardised RH_air (RH_s):{0}".format(RH_s))
    
## Standardise data point

RHD_s = (DataPoint - ym)/ystd
    
# Normalise calibration parameters

Pmax = np.max(Parameters, axis = 0)
Pmin = np.min(Parameters, axis = 0)

Cal = (Parameters - Pmin)/(Pmax - Pmin)

## Start calibration here
m = 1 # No. of data points

# params
ts = np.linspace(1, m, m)

# coordinates
xModel = np.array([0.5])
xData = np.array([0, 0.5, 1])

# calibration parameters
n = np.size(Cal,0)
  
tModel = Cal

yModel = np.zeros((n, len(xModel), len(ts)))
for i in range(n):
    yModel[i, 0, :] = RH_s[i,]

yData = np.zeros((m, len(xData)))
for i in range(m):
    yData[i, :] = np.ones(3) * RHD_s 

### implement sequential calibration
nparticles = 1000
lambda_e = 1 # same as mean of GASP parameter lambda_eta 

# load coordinates and data
cal.updateCoordinates(xModel, xData) # OK here as data all at same location

# particle filter over data outputs
beta_r = np.array([0.05,0.05,0.05])

## initialise priorSamples/posteriors
    
posteriors = np.zeros((1, nparticles, 3))
priorSamples = np.zeros((1, nparticles, 3))

cal.updateTrainingData(tModel, yModel[:, :, 0], np.reshape(yData[0, :], ((1, 3))))
cal.sequentialUpdate(nparticles, beta_r, logConstraint=np.array([0, 0, 1]))
priorSamples[0, :, :] = cal.prior
posteriors[0, :, :] = cal.posteriorSamples

ACH_OUT_ID = 0
IAS_OUT_ID = 1
LENGTH_OUT_ID = 2
print ("ACH_out type: {0}".format(type(posteriors[0,:,ACH_OUT_ID])))
print ("ACH_out shape: {0}".format(posteriors[0,:,ACH_OUT_ID].shape))

print ("ACH_out type: {0}".format(type(posteriors[0,:,IAS_OUT_ID])))
print ("ACH_out shape: {0}".format(posteriors[0,:,IAS_OUT_ID].shape))

print ("ACH_out type: {0}".format(type(posteriors[0,:,LENGTH_OUT_ID])))
print ("ACH_out shape: {0}".format(posteriors[0,:,LENGTH_OUT_ID].shape))
# # Output results
    
# df_ACH = pd.read_csv("ACH_out.csv")
# jj = np.size(df_ACH,1)+1
# df_ACH[str(jj)] = posteriors[0,:,0] 
# df_ACH.to_csv("ACH_out.csv", index=False)
    
# df_IAS = pd.read_csv("IAS_out.csv")
# df_IAS[str(jj)] = posteriors[0,:,1] 
# df_IAS.to_csv("IAS_out.csv", index=False)

# df_Length = pd.read_csv("Length_out.csv")
# df_Length[str(jj)] = posteriors[0,:,2] 
# df_Length.to_csv("Length_out.csv", index=False)


# toc = time.time()
# print(toc - tic)