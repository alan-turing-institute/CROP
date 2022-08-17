# -*- coding: utf-8 -*-
"""
Created on Mon Jun 14 09:32:23 2021

@author: rmw61
"""

from functions import derivatives, priorPPF, sat_conc
import pandas as pd
import numpy as np
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

# initialize calibration class
sigmaY = 0.5  # std measurement error GASP lambda_e
nugget = 1e-9  # same as mean GASP parameter 1/lambda_en
cal = calibration.calibrate(priorPPF, sigmaY, nugget)

### Time period for calibration
# To be run every 12 hours 3am, 3pm

tic = time.time()

p1 = 243  # start hour to test code - in CROP will be hour at which the code is run

### Calibration runs

h2 = int(p1)
h1 = int(p1 - 48)  # to take previous 10 days data

Parameters = np.genfromtxt("X.csv", delimiter=",")  # ACH,IAS pairs
NP = np.shape(Parameters)[0]

start = time.time()

results = derivatives(h1, h2, Parameters)  # runs GES model over ACH,IAS pairs

T_air = results[1, -1, :]
Cw_air = results[11, -1, :]
RH_air = Cw_air / sat_conc(T_air)

end = time.time()
print(end - start)


### Select data
### Here using historic data - will be replaced with datapoint from live database

date_cols = ["DateTimex"]
Data = pd.read_csv("TRHE2018.csv", parse_dates=date_cols)
RHData = Data["MidFarmRH2"]

dp = RHData[h2]
testdp = np.isnan(dp)

# Initialise DataPoint
LastDataPoint = pd.read_csv("DataPoint.csv")
jj = np.size(LastDataPoint, 1)

if jj > 1:
    DataPoint = float(LastDataPoint[str(jj)])
else:
    DataPoint = 0.5  # dummy value

if testdp == False:
    DataPoint = dp / 100
else:
    DataPoint = DataPoint  # takes previous value if nan recorded

LastDataPoint[str(jj + 1)] = DataPoint
LastDataPoint.to_csv("DataPoint.csv", index=False)

DT = Data["DateTimex"]
print(DT[h2])

### Run calibration

## Standardise RH_air

ym = 0.6456  # values chosen to ensure comparability against MATLAB model
ystd = 0.0675

RH_s = (RH_air - ym) / ystd

## Standardise data point

RHD_s = (DataPoint - ym) / ystd

# Normalise calibration parameters

Pmax = np.max(Parameters, axis=0)
Pmin = np.min(Parameters, axis=0)

Cal = (Parameters - Pmin) / (Pmax - Pmin)

## Start calibration here
print("Calibration ...")
start = time.time()

m = 1  # No. of data points

# params
ts = np.linspace(1, m, m)

# coordinates
xModel = np.array([0.5])
xData = np.array([0, 0.5, 1])

# calibration parameters
n = np.size(Cal, 0)

tModel = Cal

yModel = np.zeros((n, len(xModel), len(ts)))
for i in range(n):
    yModel[i, 0, :] = RH_s[
        i,
    ]

yData = np.zeros((m, len(xData)))
for i in range(m):
    yData[i, :] = np.ones(3) * RHD_s

### implement sequential calibration
nparticles = 1000
lambda_e = 1  # same as mean of GASP parameter lambda_eta

# load coordinates and data
cal.updateCoordinates(xModel, xData)  # OK here as data all at same location

# particle filter over data outputs
beta_r = np.array([0.05, 0.05, 0.05])

## initialise priorSamples/posteriors

posteriors = np.zeros((1, nparticles, 3))
priorSamples = np.zeros((1, nparticles, 3))

cal.updateTrainingData(tModel, yModel[:, :, 0], np.reshape(yData[0, :], ((1, 3))))
cal.sequentialUpdate(nparticles, beta_r, logConstraint=np.array([0, 0, 1]))
priorSamples[0, :, :] = cal.prior
posteriors[0, :, :] = cal.posteriorSamples

print("... ended")

# time
end = time.time()
print(end - start)

# Output results

df_ACH = pd.read_csv("ACH_out.csv")
jj = np.size(df_ACH, 1) + 1
df_ACH[str(jj)] = posteriors[0, :, 0]
df_ACH.to_csv("ACH_out.csv", index=False)

df_IAS = pd.read_csv("IAS_out.csv")
df_IAS[str(jj)] = posteriors[0, :, 1]
df_IAS.to_csv("IAS_out.csv", index=False)

df_Length = pd.read_csv("Length_out.csv")
df_Length[str(jj)] = posteriors[0, :, 2]
df_Length.to_csv("Length_out.csv", index=False)


toc = time.time()
print(toc - tic)
