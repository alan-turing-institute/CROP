# -*- coding: utf-8 -*-
"""
Created on Mon Jun 14 09:32:23 2021

@author: rmw61
"""

from functions_calibrationV2 import derivatives, priorPPF, sat_conc
from dataAccess import getDaysWeather, getDaysHumidityTemp, getDataPointHumidity
import pandas as pd
from pandas import DataFrame
import numpy as np
import sys,os
INVERSION_DIR = os.path.join(os.path.dirname(__file__),os.pardir,"Inversion")
sys.path.append(INVERSION_DIR)
from inversion import *
import time
import csv
import datetime

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
# This version (may_v2) downloads data from the data base and runs the model 
# calibration over the previous 20 days.

filepath_X = 'C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/X_high.csv'
filepath_weather = 'C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/ExternalWeather.csv'
filepath_TRHE = 'C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/TRHE2018_subset.csv'
filepath_datapoint = 'C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/DataPoint.csv'

useDataBase=True
DataPoint = 0.7 # Dummy value in case of nan at first point

##

# Get weather data and monitored data from database.  This code pulls in the latest 
# data, identifies the most recent common timestamp and then selects 10 days prior 
# to that for both the weather data and the monitored data.  
# Note no cleaning algorithm has yet been written, so it is assumed that 
# the data are complete.

# Weather
numDays = 25
numRows = numDays*24*6
sensorID = 27

Weather_data = getDaysWeather(numDays, numRows)
Weather_hour = pd.DataFrame(Weather_data, columns = ['DateTime','T_e', 'RH_e']).set_index('DateTime')

# Monitored Data
Monitored_data = getDaysHumidityTemp(numDays, numRows, sensorID)
Monitored_10_minutes = pd.DataFrame(Monitored_data, columns = ['DateTime','T_i','RH_i']).set_index('DateTime')

Monitored_hour = Monitored_10_minutes.resample('H').mean()
Monitored_hour.index = Monitored_hour.index.tz_convert(None) # Ensure consistency of timestamps

#  Check final timestamps for RH_hour and Weather

print(Monitored_hour[-1:].index == Weather_hour[-1:].index)

# Select oldest of the two final timestamps (or most recent 3am/3pm time 
# which occurs in both)

LatestTime = min((Monitored_hour[-1:].index), (Weather_hour[-1:].index))

print(LatestTime)

# Select data for 20 days prior to selected timestamp
deltaDays = 20
delta = datetime.timedelta(days=deltaDays)
StartTime = LatestTime - delta

t1 = StartTime.strftime("%y-%m-%d %h:%m:%s")
t2 = LatestTime.strftime("%y-%m-%d %h:%m:%s")

Monitored = Monitored_hour.loc[t1[0]:t2[0]]
Weather = Weather_hour.loc[t1[0]:t2[0]]

# Change the index so we can step through by integer and not datetime
Monitored = Monitored.reset_index()
Weather = Weather.reset_index()

df_Weather = DataFrame(Weather)
df_Weather.to_csv(r'Weather.csv',index = None, header = False)

df_Monitored = DataFrame(Monitored)
df_Monitored.to_csv(r'Monitored.csv',index = None, header = False)

##

# initialize calibration class
sigmaY = 0.5 # std measurement error GASP lambda_e
nugget = 1e-9 # same as mean GASP parameter 1/lambda_en
cal = calibration.calibrate(priorPPF, sigmaY, nugget)

### Time period for calibration
# To be run every 12 hours ideally 3am, 3pm but for now every 12 hours from 
# start of the data

tic = time.time()

p1 = 240 # start hour (11th day 240 )
ndp = 21 # number of data points 21
delta_h = 12 # hours between data points 12
p2 = (ndp-1)*delta_h+p1 # end data point 
  
seq = np.linspace(p1,p2,ndp)
sz = np.size(seq,)

# Step through each data point

for ii in range(sz):
    
### Calibration runs

    h2 = int(seq[ii])
    h1 = int(seq[ii]-239) # to take previous 10 days data 239

    Parameters = np.genfromtxt(filepath_X, delimiter=',') # ACH,IAS pairs
    NP = np.shape(Parameters)[0]
    
    start = time.time()
    print('Running model ...')

    if useDataBase:
        results = derivatives(h1, h2, Parameters, Weather) # runs GES model over ACH,IAS pairs
    else: 
        results = derivatives(h1, h2, Parameters, filePathWeather=filepath_weather) # runs GES model over ACH,IAS pairs

    #print("CSV: {0}".format(results))
    #print("Database: {0}".format(results))
    T_air = results[1,-1,:]
    Cw_air = results[11,-1,:]
    RH_air = Cw_air/sat_conc(T_air)
    
    print('... ended')
    
    
    end = time.time()
    print(end - start)

## Initialise DataPoint for calibration
    
    DataPoint = Monitored.RH_i[h2]
    testdp = np.isnan(DataPoint)
    print(testdp)
    print(DataPoint)
    
    if testdp == False:
        DataPoint = DataPoint/100
    else:
        DataPoint = DataPoint # takes previous value if nan recorded

    print("DataPoint:{0}".format(DataPoint))
    
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
    print('Calibration ...')
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
    nparticles = 1000 # will be 1000
    lambda_e = 1 # same as mean of GASP parameter lambda_eta 

# load coordinates and data
    cal.updateCoordinates(xModel, xData) # OK here as data all at same location

# particle filter over data outputs
    beta_r = np.array([0.05,0.05,0.05])

## initialise priorSamples/posteriors
    if ii == 0:
        posteriors = np.zeros((sz, nparticles, 3))
        priorSamples = np.zeros((sz, nparticles, 3))
        mlSamples = np.zeros((sz, nparticles))
        wSamples = np.zeros((sz, nparticles))
        indsSamples = np.zeros((sz, nparticles))

    cal.updateTrainingData(tModel, yModel[:, :, 0], np.reshape(yData[0, :], ((1, 3))))
    cal.sequentialUpdate(nparticles, beta_r, logConstraint=np.array([0, 0, 1]))
    priorSamples[ii, :, :] = cal.prior
    posteriors[ii, :, :] = cal.posteriorSamples
    mlSamples[ii, :] = cal.mlS
    wSamples[ii, :] = cal.wS
    indsSamples[ii, :] = cal.inds
    print('... ended')

    posterior_ACH = posteriors[ii,:,0]
    posterior_IAS = posteriors[ii,:,1]
    posterior_length = posteriors[ii,:,2]
    
    df = pd.read_csv("ACH_out.csv")
    df[str(ii)] = posteriors[ii,:,0] 
    df.to_csv("ACH_out.csv", index=False)
    
    df = pd.read_csv("IAS_out.csv")
    df[str(ii)] = posteriors[ii,:,1] 
    df.to_csv("IAS_out.csv", index=False)
 
    df = pd.read_csv("Length_out.csv")
    df[str(ii)] = posteriors[ii,:,2] 
    df.to_csv("Length_out.csv", index=False)
 
    
# Output results

df_ACH = DataFrame(posteriors[:,:,0])
df_ACH.to_csv(r'ACH_12.csv',index = None, header = False) # p = python

prior_ACH = priorSamples[:,:,0]
df_priorACH = DataFrame(prior_ACH)
df_priorACH.to_csv(r'priorACH_12.csv',index = None, header = False)
#
df_IAS = DataFrame(posteriors[:,:,1])
df_IAS.to_csv(r'IAS_12.csv',index = None, header = False)

prior_IAS = priorSamples[:,:,1]
df_priorIAS = DataFrame(prior_IAS)
df_priorIAS.to_csv(r'priorIAS_12.csv',index = None, header = False)
#
df_Length = DataFrame(posteriors[:,:,2])
df_Length.to_csv(r'Length_12.csv',index = None, header = False)

prior_Length = priorSamples[:,:,2]
df_priorLength = DataFrame(prior_Length)
df_priorLength.to_csv(r'priorLength_12.csv',index = None, header = False)

df_Weather = DataFrame(Weather)
df_Weather.to_csv(r'Weather_12.csv',index = None, header = False) # p = python

df_Monitored = DataFrame(Monitored)
df_Monitored.to_csv(r'Monitored_12.csv',index = None, header = False) # p = python


#    


#ACH_OUT_ID = 0
#IAS_OUT_ID = 1
#LENGTH_OUT_ID = 2
#print ("ACH_out type: {0}".format(type(posteriors[0,:,ACH_OUT_ID])))
#print ("ACH_out shape: {0}".format(posteriors[0,:,ACH_OUT_ID].shape))

#print ("ACH_out type: {0}".format(type(posteriors[0,:,IAS_OUT_ID])))
#print ("ACH_out shape: {0}".format(posteriors[0,:,IAS_OUT_ID].shape))

#print ("ACH_out type: {0}".format(type(posteriors[0,:,LENGTH_OUT_ID])))
#print ("ACH_out shape: {0}".format(posteriors[0,:,LENGTH_OUT_ID].shape))

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