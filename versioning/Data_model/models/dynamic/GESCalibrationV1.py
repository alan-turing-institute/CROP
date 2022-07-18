# -*- coding: utf-8 -*-
"""
Created on Mon Jun 14 09:32:23 2021

@author: rmw61
"""

from ges.functionsV2 import derivatives, priorPPF, sat_conc
from ges.dataAccess import getDaysWeather, getDaysHumidityTemp, getDataPointHumidity
import pandas as pd
from pandas import DataFrame
import numpy as np
from pathlib import Path
import logging

from inversion import *
import time
import csv
import datetime
from ges.config import config


def main():
    np.random.seed(1000)
    logging.basicConfig(level=logging.INFO)

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

    path_conf = config(section="paths")
    data_dir = Path(path_conf["data_dir"])
    filepath_X = data_dir / path_conf["filename_x"]
    filepath_Weather = data_dir / path_conf["filename_weather"]
    filepath_Monitored = data_dir / path_conf["filename_monitored"]
    filepath_LastDataPoint = data_dir / path_conf["filename_lastdatapoint"]
    filepath_ACH = data_dir / path_conf["filename_ach"]
    filepath_IAS = data_dir / path_conf["filename_ias"]
    filepath_Length = data_dir / path_conf["filename_length"]
    filepath_ACHprior = data_dir / path_conf["filename_achprior"]
    filepath_IASprior = data_dir / path_conf["filename_iasprior"]
    filepath_Lengthprior = data_dir / path_conf["filename_lengthprior"]

    tic = time.time()

    useDataBase = True
    DataPoint = 0.7  # Dummy value in case of nan at first point

    ##

    cal_conf = config(section="calibration")

    # Get weather data and monitored data from database.  This code pulls in the latest
    # data, identifies the most recent common timestamp and then selects 10 days prior
    # to that for both the weather data and the monitored data.
    # Note no cleaning algorithm has yet been written, so it is assumed that
    # the data are complete.

    # Weather
    num_weather_days = int(cal_conf["num_weather_days"])
    # The 6 is because weather data is read for every 10 minutes.
    num_weather_rows = num_weather_days * 24 * 6
    sensorID = int(cal_conf["sensor_id"])

    Weather_data = getDaysWeather(num_weather_days, num_weather_rows)
    Weather_hour = pd.DataFrame(
        Weather_data, columns=["DateTime", "T_e", "RH_e"]
    ).set_index("DateTime")

    # Monitored Data
    Monitored_data = getDaysHumidityTemp(
        num_weather_days, num_weather_rows, cal_conf["sensor_id"]
    )
    Monitored_10_minutes = pd.DataFrame(
        Monitored_data, columns=["DateTime", "T_i", "RH_i"]
    ).set_index("DateTime")

    Monitored_hour = Monitored_10_minutes.resample("H").mean()
    try:
        Monitored_hour.index = Monitored_hour.index.tz_convert(
            None
        )  # Ensure consistency of timestamps
    except TypeError:
        # If the index is already time zone naive.
        pass

    # Check final timestamps for RH_hour and Weather

    logging.info(Monitored_hour[-1:].index == Weather_hour[-1:].index)

    # Select oldest of the two final timestamps (or most recent 3am/3pm time
    # which occurs in both)

    LatestTime = min((Monitored_hour.index[-1]), (Weather_hour.index[-1]))

    # Identify start hour to feed into light setting
    LatestTimeHourValue = float(LatestTime.hour)

    # Select data for 20 days prior to selected timestamp
    deltaDays = int(cal_conf["delta_days"])
    delta = datetime.timedelta(days=deltaDays)
    StartTime = LatestTime - delta

    Monitored = Monitored_hour.loc[StartTime:LatestTime]
    Weather = Weather_hour.loc[StartTime:LatestTime]

    # Change the index so we can step through by integer and not datetime
    Monitored = Monitored.reset_index()
    Weather = Weather.reset_index()

    df_Weather = DataFrame(Weather)
    df_Weather.to_csv(filepath_Weather, index=None, header=False)

    df_Monitored = DataFrame(Monitored)
    df_Monitored.to_csv(filepath_Monitored, index=None, header=False)

    ##

    # initialize calibration class
    sigmaY = float(cal_conf["sigma_y"])  # std measurement error GASP lambda_e
    nugget = float(cal_conf["nugget"])  # same as mean GASP parameter 1/lambda_en
    cal = calibration.calibrate(priorPPF, sigmaY, nugget)

    ### Time period for calibration
    # To be run every 12 hours ideally 3am, 3pm but for now every 12 hours from
    # start of the data

    calibration_window_days = int(cal_conf["calibration_window_days"])
    p1 = 24 * calibration_window_days  # start hour
    ndp = int(cal_conf["num_data_points"])  # number of data points
    delta_h = int(cal_conf["delta_h"])  # hours between data points
    p2 = (ndp - 1) * delta_h + p1  # end data point

    seq = np.linspace(p1, p2, ndp)

    # Step through each data point

    LastDataPoint = pd.DataFrame()

    for ii in range(ndp):

        ### Calibration runs

        h2 = int(seq[ii])
        # TODO Why the -1?
        h1 = int(seq[ii] - (calibration_window_days * 24 - 1))

        Parameters = np.genfromtxt(
            cal_conf["ach_ias_pairs"].split(";"), delimiter=","
        )  # ACH,IAS pairs
        NP = np.shape(Parameters)[0]

        start = time.time()
        logging.info("Running model ...")

        if useDataBase:
            results = derivatives(
                h1, h2, Parameters, Weather, LatestTimeHourValue
            )  # runs GES model over ACH,IAS pairs
        else:
            results = derivatives(
                h1, h2, Parameters, filePathWeather=filepath_weather
            )  # runs GES model over ACH,IAS pairs

        # logging.info("CSV: {0}".format(results))
        # logging.info("Database: {0}".format(results))
        T_air = results[1, -1, :]
        Cw_air = results[11, -1, :]
        RH_air = Cw_air / sat_conc(T_air)

        logging.info("... ended")

        end = time.time()
        logging.info(end - start)

        ## Initialise DataPoint for calibration

        DataPoint = Monitored.RH_i[h2]
        testdp = np.isnan(DataPoint)
        # logging.info(testdp)
        # logging.info(DataPoint)

        if testdp == False:
            # Divide by 100 to convert percentages to ratios
            DataPoint = DataPoint / 100
        else:
            # takes previous value if nan recorded
            DataPoint = (LastDataPoint[-1:]).DataPoint[0]

        logging.info("DataPoint:{0}".format(DataPoint))

        dpnew = pd.DataFrame({"DataPoint": DataPoint}, {Monitored.DateTime[h2]})
        LastDataPoint = LastDataPoint.append(dpnew)

        # DT = Data['DateTimex']
        # logging.info(DT[h2])

        # ### Run calibration

        # ## Standardise RH_air
        # values chosen to ensure comparability against MATLAB model
        ym = float(cal_conf["ym"])
        ystd = float(cal_conf["ystd"])

        RH_s = (RH_air - ym) / ystd
        logging.info("Standardised RH_air (RH_s):{0}".format(RH_s))

        ## Standardise data point

        RHD_s = (DataPoint - ym) / ystd

        # Normalise calibration parameters

        Pmax = np.max(Parameters, axis=0)
        Pmin = np.min(Parameters, axis=0)

        Cal = (Parameters - Pmin) / (Pmax - Pmin)

        ## Start calibration here
        logging.info("Calibration ...")
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
            yModel[i, 0, :] = RH_s[i]

        yData = np.zeros((m, len(xData)))
        for i in range(m):
            yData[i, :] = np.ones(3) * RHD_s

        ### implement sequential calibration
        nparticles = 1000  # will be 1000
        lambda_e = 1  # same as mean of GASP parameter lambda_eta

        # load coordinates and data
        cal.updateCoordinates(xModel, xData)  # OK here as data all at same location

        # particle filter over data outputs
        beta_r = np.array([0.05, 0.05, 0.05])

        ## initialise priorSamples/posteriors
        if ii == 0:
            posteriors = np.zeros((ndp, nparticles, 3))
            priorSamples = np.zeros((ndp, nparticles, 3))
            mlSamples = np.zeros((ndp, nparticles))
            wSamples = np.zeros((ndp, nparticles))
            indsSamples = np.zeros((ndp, nparticles))

        cal.updateTrainingData(
            tModel, yModel[:, :, 0], np.reshape(yData[0, :], ((1, 3)))
        )
        cal.sequentialUpdate(nparticles, beta_r, logConstraint=np.array([0, 0, 1]))
        priorSamples[ii, :, :] = cal.prior
        posteriors[ii, :, :] = cal.posteriorSamples
        mlSamples[ii, :] = cal.mlS
        wSamples[ii, :] = cal.wS
        indsSamples[ii, :] = cal.inds
        logging.info("... ended")

        posterior_ACH = posteriors[ii, :, 0]
        posterior_IAS = posteriors[ii, :, 1]
        posterior_length = posteriors[ii, :, 2]

        try:
            df = pd.read_csv(filepath_ACH)
        except FileNotFoundError:
            df = pd.DataFrame()
        df[str(ii)] = posteriors[ii, :, 0]
        df.to_csv(filepath_ACH, index=False)

        try:
            df = pd.read_csv(filepath_IAS)
        except FileNotFoundError:
            df = pd.DataFrame()
        df[str(ii)] = posteriors[ii, :, 1]
        df.to_csv(filepath_IAS, index=False)

        try:
            df = pd.read_csv(filepath_Length)
        except FileNotFoundError:
            df = pd.DataFrame()
        df[str(ii)] = posteriors[ii, :, 2]
        df.to_csv(filepath_Length, index=False)

    # Time
    toc = time.time()
    logging.info(toc - tic)

    # Output priors and data

    prior_ACH = priorSamples[:, :, 0]
    df_priorACH = DataFrame(prior_ACH)
    df_priorACH.to_csv(filepath_ACHprior, index=None, header=False)
    #

    prior_IAS = priorSamples[:, :, 1]
    df_priorIAS = DataFrame(prior_IAS)
    df_priorIAS.to_csv(filepath_IASprior, index=None, header=False)
    #

    prior_Length = priorSamples[:, :, 2]
    df_priorLength = DataFrame(prior_Length)
    df_priorLength.to_csv(filepath_Lengthprior, index=None, header=False)

    df_Weather = DataFrame(Weather)
    df_Weather.to_csv(filepath_Weather, index=None, header=False)  # p = python

    df_Monitored = DataFrame(Monitored)
    df_Monitored.to_csv(filepath_Monitored, index=None, header=False)  # p = python

    LastDataPoint = LastDataPoint.reset_index()
    LastDataPoint.to_csv(filepath_LastDataPoint, index=None, header=False)
    #


if __name__ == "__main__":
    main()
