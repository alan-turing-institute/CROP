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
# NB code takes ~36 hours to run full year if tolerance is 1e-5 (15 mins per step if
# tolerance is 1e-6)

# initialize calibration class
sigmaY = 0.5  # std measurement error GASP lambda_e
nugget = 1e-9  # same as mean GASP parameter 1/lambda_en
cal = calibration.calibrate(priorPPF, sigmaY, nugget)

### Time period for calibration
# Every 12 hours 3am, 3pm, starting on 11th January

tic = time.time()

p1 = 243  # start hour (3am on 11th January)
ndp = 710  # number of data points
delta_h = 12  # hours between data points
p2 = (ndp - 1) * delta_h + p1  # end data point (3pm on 31st December)

seq = np.linspace(p1, p2, ndp)
sz = np.size(
    seq,
)

# Step through each data point

for ii in range(sz):

    ### Calibration runs

    h2 = int(seq[ii])
    h1 = int(seq[ii] - 240)  # to take previous 10 days data

    Parameters = np.genfromtxt("X.csv", delimiter=",")  # ACH,IAS pairs
    NP = np.shape(Parameters)[0]

    start = time.time()

    results = derivatives(
        h1, h2, Parameters, ndp, 0, 0, 1
    )  # runs GES model over ACH,IAS pairs

    T_air = results[1, -1, :]
    Cw_air = results[11, -1, :]
    RH_air = Cw_air / sat_conc(T_air)

    # RH_air = results[0]

    end = time.time()
    print(end - start)

    ### Select data

    date_cols = ["DateTimex"]
    Data = pd.read_csv("TRHE2018.csv", parse_dates=date_cols)
    RHData = Data["MidFarmRH2"]

    dp = RHData[h2]
    testdp = np.isnan(dp)

    if testdp == False:
        DataPoint = dp / 100
    else:
        DataPoint = DataPoint  # takes previous value if nan recorded

    DT = Data["DateTimex"]
    print(DT[h2])

    ### Run calibration

    ## Standardise RH_air

    # ym = np.mean(RH_air)
    # ystd = np.std(RH_air)

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
    print("... ended")

    # time
    end = time.time()
    print(end - start)

    ###
    posterior_ACH = posteriors[ii, :, 0]
    posterior_IAS = posteriors[ii, :, 1]
    posterior_length = posteriors[ii, :, 2]

    df = pd.read_csv("ACH_out.csv")
    df[str(ii)] = posteriors[ii, :, 0]
    df.to_csv("ACH_out.csv", index=False)

    df = pd.read_csv("IAS_out.csv")
    df[str(ii)] = posteriors[ii, :, 1]
    df.to_csv("IAS_out.csv", index=False)


# Output results

from pandas import DataFrame

df_ACH = DataFrame(posteriors[:, :, 0])
df_ACH.to_csv(r"ACH_p_1.csv", index=None, header=False)  # p = python

prior_ACH = priorSamples[:, :, 0]
df_priorACH = DataFrame(prior_ACH)
df_priorACH.to_csv(r"priorACH_p_1.csv", index=None, header=False)
#
df_IAS = DataFrame(posteriors[:, :, 1])
df_IAS.to_csv(r"IAS_p_1.csv", index=None, header=False)

prior_IAS = priorSamples[:, :, 1]
df_priorIAS = DataFrame(prior_IAS)
df_priorIAS.to_csv(r"priorIAS_p_1.csv", index=None, header=False)
#
df_Length = DataFrame(posteriors[:, :, 2])
df_Length.to_csv(r"Length_p_1.csv", index=None, header=False)

prior_Length = priorSamples[:, :, 2]
df_priorLength = DataFrame(prior_Length)
df_priorLength.to_csv(r"priorLength_p_1.csv", index=None, header=False)
#

toc = time.time()
print(toc - tic)
