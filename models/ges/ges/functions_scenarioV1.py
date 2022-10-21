# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 09:18:07 2021

@author: rmw61
"""
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import datetime
import calendar
from .parameters import T_k, deltaT
from .parameters import R, M_w, M_a, atm, H_fg, N_A, heat_phot, Le
from .parameters import V, A_c, A_f, A_v, A_m, A_p, A_l
from .parameters import d_c, d_f, d_m, d_p, cd_c, c_i, c_f, c_m, c_p
from .parameters import F_c_f, F_f_c, F_c_v, F_c_m, F_l_c, F_l_v, F_l_m, F_l_p
from .parameters import F_m_l, F_f_p, F_c_l, F_m_v, F_v_l, F_p_l
from .parameters import F_p_f, F_p_v, F_p_m, F_v_c, F_v_p, F_v_m, F_m_c, F_m_p
from .parameters import eps_c, eps_f, eps_v, eps_m, eps_p, eps_l
from .parameters import rho_c, rho_f, rho_v, rho_m, rho_p, rho_l
from .parameters import lam_c, l_c, rhod_c, c_c, lam_f, l_f, lam_p, l_m
from .parameters import T_ss, T_al
from .parameters import f_heat, f_light, P_al, P_ambient_al, P_dh
from .parameters import c_v, msd_v, d_v, AF_g, LAI, dsat
from scipy.integrate import solve_ivp
from .config import config

from inversion import *
from .dataAccess import getDaysWeather, getDaysWeatherForecast

path_conf = config(section="paths")

DATA_DIR = Path(path_conf["data_dir"])
FILEPATH_WEATHER = DATA_DIR / path_conf["filename_weather"]
FILEPATH_WEATHER_FORECAST = DATA_DIR / path_conf["filename_weather_forecast"]
FILEPATH_ACH = DATA_DIR / path_conf["filename_ach"]
FILEPATH_IAS = DATA_DIR / path_conf["filename_ias"]
FILEPATH_LEN = DATA_DIR / path_conf["filename_length"]

CAL_CONF = config(section="calibration")

def DatetimeToTimestamp(d):
    """
    Uses calendar module to convert Python datetime to epoch
    """
    return calendar.timegm(d.timetuple())

def TimestampToDatetime(d):
    """
    Uses datetime module to convert epoch to Python datetime (UTC)
    """
    return datetime.datetime.utcfromtimestamp(d)

def StringToDatetime(d):
    """
    Uses datetime module to convert string to Python datetime
    Note the string must be in the format: "%Y-%m-%d %H:%M:%S"
    """
    return datetime.datetime.strptime(d, "%Y-%m-%d %H:%M:%S")


def climterp_linear(h1, h2, numDays, filepath_weather=None):
    temp_in = None
    rh_in = None
    if filepath_weather:
        header_list = ["DateTime", "T_e", "RH_e"]
        ExternalWeather = pd.read_csv(
            filepath_weather, delimiter=",", names=header_list
        )
        # ExternalWeather = np.genfromtxt(filepath_weather, delimiter=',')
        # temp_in = ExternalWeather[h1:h2+1,1] # +1 to ensure correct end point
        # rh_in = ExternalWeather[h1:h2+1,2] # +1 to ensure correct end point
        timestamp = ExternalWeather.DateTime
        timestamp = timestamp.to_numpy()
        timestamp = np.array([StringToDatetime(timestamp[d]) for d in range(0, timestamp.shape[0])])
        temp_in = ExternalWeather.T_e
        temp_in = temp_in.to_numpy().astype(np.float64)
        rh_in = ExternalWeather.RH_e
        rh_in = rh_in.to_numpy().astype(np.float64)
    else:
        ExternalWeather = np.asarray(
            getDaysWeather(numDays + 1, numRows=(numDays + 1) * 24)
        )
        timestamp = ExternalWeather[:, 0]
        temp_in = ExternalWeather[:, 1].astype(
            np.float64
        )  # +1 to ensure correct end point
        rh_in = ExternalWeather[:, 2].astype(
            np.float64
        )  # +1 to ensure correct end point

    # remove nans
    # nans, x= nan_helper(temp_in)
    # temp_in[nans]= np.interp(x(nans), x(~nans), temp_in[~nans])

    # nans, x= nan_helper(rh_in)
    # rh_in[nans]= np.interp(x(nans), x(~nans), rh_in[~nans])

    # convert Python datetime to epoch - this allows for linear interpolation of time
    timestamp = np.array([DatetimeToTimestamp(timestamp[d]) for d in range(0, timestamp.shape[0])])
    ind = h2 - h1 + 1
    seconds_in_hour = 3600
    seconds_in_hspan = (h2 - h1) * seconds_in_hour
    # `t` corresponds to the time vector for the hourly weather data pulled from the DB
    t = np.linspace(0, seconds_in_hspan, ind)  # TODO This is really just a range.
    # `mult` corresponds to the resampling time vector (at frequency corresponding to period `deltaT`)
    mult = np.linspace(0, seconds_in_hspan, int(1 + seconds_in_hspan / deltaT))
    # perform linear interpolation
    clim_timestamp = np.interp(mult, t, timestamp[-ind:])
    clim_timestamp = np.array([TimestampToDatetime(clim_timestamp[d]) for d in range(0, clim_timestamp.shape[0])]) # convert back to datetime
    clim_t = np.interp(mult, t, temp_in[-ind:])
    clim_rh = np.interp(mult, t, rh_in[-ind:])
    climate = np.vstack((clim_timestamp, clim_t, clim_rh))
    return climate


def climterp_forecast_linear(numDays=2, filepath_weather_forecast=None):
    """
    Perform linear interpolation of weather forecast data.

    Arguments:
        numDays: number of days into the future for which to retrieve weather forecasts.
            Default value is 2. Weather forecasts are available for a maximum of 2 days
            into the future.
        filepath_weather_forecast: path of csv file containing weather forecasts.
            If no path is provided, the function retrieves weather forecast data from the DB.
    Returns:
        climate: numpy array containing the linearly interpolated weather forecasts.
        The first row contains the timestamps, the second row contains temperature
        and the third row contains relative humidity.
    """
    timestamp = None
    temp_in = None
    rh_in = None
    if filepath_weather_forecast:
        header_list = ["DateTime", "T_e", "RH_e"]
        ExternalWeather = pd.read_csv(
            filepath_weather_forecast, delimiter=",", names=header_list
        )
        timestamp = ExternalWeather.DateTime
        timestamp = timestamp.to_numpy()
        timestamp = np.array([StringToDatetime(timestamp[d]) for d in range(0, timestamp.shape[0])])
        temp_in = ExternalWeather.T_e
        temp_in = temp_in.to_numpy().astype(np.float64)
        rh_in = ExternalWeather.RH_e
        rh_in = rh_in.to_numpy().astype(np.float64)
    else:
        ExternalWeather = getDaysWeatherForecast(numDays)
        ExternalWeather = np.asarray(ExternalWeather)
        timestamp = ExternalWeather[:, 0]
        temp_in = ExternalWeather[:, 1].astype(
            np.float64
        )  # +1 to ensure correct end point
        rh_in = ExternalWeather[:, 2].astype(
            np.float64
        )  # +1 to ensure correct end point
    delta_in_secs = timestamp[-1] - timestamp[0]
    delta_in_secs = delta_in_secs.total_seconds()
    # `t` corresponds to the time vector for the hourly weather data pulled from the DB
    t = np.linspace(0, delta_in_secs, len(timestamp))
    # `mult` corresponds to the resampling time vector (at frequency corresponding to period `deltaT`)
    mult = np.linspace(0, delta_in_secs, int(1 + delta_in_secs / deltaT))
    # convert Python datetime to epoch - this allows for linear interpolation of time
    timestamp = np.array([DatetimeToTimestamp(timestamp[d]) for d in range(0, timestamp.shape[0])])
    # perform linear interpolation
    clim_timestamp = np.interp(mult, t, timestamp)
    clim_timestamp = np.array([TimestampToDatetime(clim_timestamp[d]) for d in range(0, clim_timestamp.shape[0])])
    clim_t = np.interp(mult, t, temp_in)
    clim_rh = np.interp(mult, t, rh_in)
    climate = np.vstack((clim_timestamp, clim_t, clim_rh))
    return climate


def lamorturb(Gr, Re):

    Le = 0.819

    free = Gr < 1e5
    Nu_G = 0.5 * free * Gr**0.25 + 0.13 * (1 - free) * Gr**0.33

    forced = Re < 2e4
    Nu_R = 0.6 * forced * Re**0.5 + 0.032 * (1 - forced) * Re**0.8

    x = Nu_G > Nu_R

    Nu = x * Nu_G + (1 - x) * Nu_R

    Sh = x * Nu * Le**0.25 + (1 - x) * Nu * Le**0.33

    return (Nu, Sh)


def convection(d, A, T1, T2, ias):

    g = 9.81
    nu = 15.1e-6
    lam = 0.025

    Gr = (g * d**3) / (T1 * nu**2) * abs(T1 - T2)
    Re = ias * d / nu
    (Nu, Sh) = lamorturb(Gr, Re)

    QV_1_2 = A * Nu * lam * (T1 - T2) / d
    QP_1_2 = 0

    return (QV_1_2, QP_1_2)


def radiation(eps_1, eps_2, rho_1, rho_2, F_1_2, F_2_1, A_1, T_1, T_2):

    sigm = 5.67e-8

    k = eps_1 * eps_2 / (1 - rho_1 * rho_2 * F_1_2 * F_2_1)
    QR_1_2 = k * sigm * A_1 * F_1_2 * (T_1**4 - T_2**4)

    return QR_1_2


def conduction(A, lam, l, T1, T2):
    QD_12 = (A * lam / l) * (T1 - T2)

    return QD_12


# def T_ext(t):
#    # Weather data
#
#   climate = np.genfromtxt('climate.txt', delimiter=',')

#    n = int(np.ceil(t/deltaT))
#    T_e = climate[n, 0] + T_k

#    return(T_e)


def sat_conc(T):

    TC = T - T_k
    spec_hum = np.exp(11.56 - 4030 / (TC + 235))
    air_dens = -0.0046 * TC + 1.2978
    a = spec_hum * air_dens

    return a


# def Cw_ext(t):
# Weather data

#    climate = np.genfromtxt('climate.txt', delimiter=',')

#    n = int(np.ceil(t/deltaT))
#    RH_e = climate[n, 1]/100;

#    Cw_e = RH_e * sat_conc(T_ext(t))

#    return(Cw_e)


def nan_helper(y):
    """Helper to handle indices and logical indices of NaNs.

    Input:
        - y, 1d numpy array with possible NaNs
    Output:
        - nans, logical indices of NaNs
        - index, a function, with signature indices= index(logical_indices),
          to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    """

    return np.isnan(y), lambda z: z.nonzero()[0]


def day(t):
    ## Day
    day_new = np.ceil(t / 86400)
    return day_new


def model(
    t,
    z,
    climate,
    ACHvec,
    iasvec,
    daynum,
    count,
    h1,
    h2,
    ndhvec,
    lshiftvec,
    LatestTimeHourValue,
):
    delta_h = int(CAL_CONF["delta_h"])

    T_c = z[0]
    T_i = z[1]
    T_v = z[2]
    T_m = z[3]
    T_p = z[4]
    T_f = z[5]
    T_c1 = z[6]
    T_c2 = z[7]
    T_c3 = z[8]
    T_c4 = z[9]
    T_c5 = z[10]
    C_w = z[11]

    p_w = C_w * R * T_i / M_w
    rho_i = ((atm - p_w) * M_a + p_w * M_w) / (R * T_i)

    t_init = h1 * 3600

    n = int(np.ceil((t - t_init) / deltaT))
    T_ext = climate[n, 0] + T_k
    RH_e = climate[n, 1] / 100
    Cw_ext = RH_e * sat_conc(T_ext)

    daynum.append(day(t))
    # if daynum[(len(daynum)-1)] > daynum[(len(daynum)-2)]:
    #    logging.info(daynum[len(daynum)-1])

    # Set ACH,ias
    hour = np.floor(t / 3600) + 1
    # TODO What are these bounds? Should they depend on delta_h in this way?
    seq = range(h1 + delta_h, h2 + 24, delta_h)

    if hour >= seq[count[-1]]:
        count_new = count[-1] + 1
        count.append(count_new)

    ACH = ACHvec[count[-1]]
    ias = iasvec[count[-1]]
    ndh = ndhvec[count[-1]]
    lshift = lshiftvec[count[-1]]

    ## Lights
    day_hour = (
        (hour + LatestTimeHourValue) / 24 - np.floor((hour + LatestTimeHourValue) / 24)
    ) * 24
    L_on = (day_hour > -0.01 and day_hour < (08.01 + lshift)) or day_hour > (
        15.01 + lshift
    )
    AL_on = day_hour > 08.01 and day_hour < 16.01

    T_l = L_on * T_al + (1 - L_on) * T_i

    QV_l_i = f_heat * P_al * L_on + P_ambient_al * AL_on + ndh * P_dh

    ## Convection
    # Convection internal air -> cover

    (QV_i_c, QP_i_c) = convection(d_c, A_c, T_i, T_c, ias)

    # Convection internal air -> floor

    (QV_i_f, QP_i_f) = convection(d_f, A_f, T_i, T_f, ias)

    # Convection internal air -> vegetation
    A_v_exp = LAI * A_v
    (QV_i_v, QP_i_v) = convection(d_v, A_v_exp, T_i, T_v, ias)

    # Convection internal air -> mat
    A_m_exp = A_m * (1 - AF_g)
    (QV_i_m, QP_i_m) = convection(d_m, A_m_exp * 0.6, T_i, T_m, ias)

    # QP_i_m non-zero so calculate here
    g = 9.81
    nu = 15.1e-6
    lam = 0.025
    Gr = (g * d_m**3) / (T_i * nu**2) * abs(T_i - T_m)
    Re = ias * d_m / nu
    (Nu, Sh) = lamorturb(Gr, Re)

    QP_i_m = (
        A_m_exp
        * 0.4
        * dsat
        * H_fg
        / (rho_i * c_i)
        * (Sh / Le)
        * (lam / d_m)
        * (C_w - sat_conc(T_m))
    )

    # Convection internal air -> tray

    (QV_i_p, QP_i_p) = convection(d_p, A_p, T_i, T_p, ias)

    ## Radiation
    # Radiation cover to floor
    QR_c_f = radiation(eps_c, eps_f, rho_c, rho_f, F_c_f, F_f_c, A_c, T_c, T_f)

    # Radiation cover to vegetation
    QR_c_v = radiation(eps_c, eps_v, rho_c, rho_v, F_c_v, F_v_c, A_c, T_c, T_v)

    # Radiation cover to mat
    QR_c_m = radiation(eps_c, eps_m, rho_c, rho_m, F_c_m, F_m_c, A_c, T_c, T_m)

    # Radiation lights to cover
    QR_l_c = radiation(eps_l, eps_c, rho_l, rho_c, F_l_c, F_c_l, A_l, T_l, T_c)

    # Radiation lights to vegetation
    QR_l_v = radiation(eps_l, eps_v, rho_l, rho_v, F_l_v, F_v_l, A_l, T_l, T_v)

    # Radiation lights to mat
    QR_l_m = radiation(eps_l, eps_m, rho_l, rho_m, F_l_m, F_m_l, A_l, T_l, T_m)

    # Radiation lights to tray
    QR_l_p = radiation(eps_l, eps_p, rho_l, rho_p, F_l_p, F_p_l, A_l, T_l, T_p)

    # Radiation vegetation to cover
    QR_v_c = radiation(eps_v, eps_c, rho_v, rho_c, F_v_c, F_c_v, A_v, T_v, T_c)

    # Radiation vegetation to mat
    QR_v_m = radiation(eps_v, eps_m, rho_v, rho_m, F_v_m, F_m_v, A_v, T_v, T_m)

    # Radiation vegetation to tray
    QR_v_p = radiation(eps_v, eps_p, rho_v, rho_p, F_v_p, F_p_v, A_v, T_v, T_p)

    # Radiation mat to cover
    QR_m_c = radiation(eps_m, eps_c, rho_m, rho_c, F_m_c, F_c_m, A_m, T_m, T_c)

    # Radiation mat to vegetation
    QR_m_v = radiation(eps_m, eps_v, rho_m, rho_v, F_m_v, F_v_m, A_m, T_m, T_v)

    # Radiation mat to tray
    QR_m_p = radiation(eps_m, eps_p, rho_m, rho_p, F_m_p, F_p_m, A_m, T_m, T_p)

    # Radiation tray to vegetation
    QR_p_v = radiation(eps_p, eps_v, rho_p, rho_v, F_p_v, F_v_p, A_p, T_p, T_v)

    # Radiation tray to mat
    QR_p_m = radiation(eps_p, eps_m, rho_p, rho_m, F_p_m, F_m_p, A_p, T_p, T_m)

    # Radiation tray to floor
    QR_p_f = radiation(eps_p, eps_f, rho_p, rho_f, F_p_f, F_f_p, A_p, T_p, T_f)

    # Radiation floor to cover
    QR_f_c = radiation(eps_f, eps_c, rho_f, rho_c, F_f_c, F_c_f, A_f, T_f, T_c)

    # Radiation floor to tray
    QR_f_p = radiation(eps_f, eps_p, rho_f, rho_p, F_f_p, F_p_f, A_f, T_f, T_p)

    ## Conduction
    # Conduction through cover
    QD_c12 = conduction(A_c, lam_c[0], l_c[0], T_c, T_c1)
    QD_c23 = conduction(A_c, lam_c[1], l_c[1], T_c1, T_c2)
    QD_c34 = conduction(A_c, lam_c[2], l_c[2], T_c2, T_c3)
    QD_c45 = conduction(A_c, lam_c[3], l_c[3], T_c3, T_c4)
    QD_c56 = conduction(A_c, lam_c[4], l_c[4], T_c4, T_c5)
    QD_c67 = conduction(A_c, lam_c[5], l_c[5], T_c5, T_ss)

    # Conduction through floor
    T_fl = (0.435 * (T_ext - T_k) + 12) + T_k
    QD_f12 = conduction(A_f, lam_f, l_f, T_f, T_fl)

    # Conduction mat to tray
    QD_m_p = (A_m * lam_p / l_m) * (T_m - T_p)

    ## Transpiration
    QS_int = f_light * P_al * L_on / A_p

    PPFD = QS_int / 1e-6 / N_A / heat_phot
    r_aG = 100
    r_sG = 60 * (1500 + PPFD) / (200 + PPFD)
    QT_G = A_v * (1 * LAI * H_fg * (1 / (r_aG + r_sG)) * (sat_conc(T_v) - C_w))

    QT_v_i = QT_G

    ## Ventilation

    QV_i_e = ACH * V * rho_i * c_i * (T_i - T_ext)

    MW_i_e = ACH * (C_w - Cw_ext)

    ## Dehumidification

    RH = C_w / sat_conc(T_i)
    dehumidify = ndh * (0.07 * T_i + 5 * RH - 21.8) / V

    MW_cc_i = -1 * dehumidify / 3600

    # logging.info(MW_i_e)

    # ODE equations

    dT_cdt = (1 / (A_c * cd_c)) * (QV_i_c - QR_c_f - QR_c_v - QR_c_m + QR_l_c - QD_c12)
    dT_idt = (1 / (V * rho_i * c_i)) * (
        -QV_i_c - QV_i_f - QV_i_e + QV_l_i - QV_i_m - QV_i_v - QV_i_p
    )
    dT_fdt = (1 / (A_f * c_f)) * (QV_i_f - QR_f_c - QR_f_p - QD_f12)
    dT_vdt = (1 / (c_v * A_v * msd_v)) * (
        QV_i_v - QR_v_c - QR_v_m + QR_l_v - QR_v_p - QT_v_i
    )
    dT_mdt = (1 / (A_m * c_m)) * (
        QV_i_m + QP_i_m - QR_m_v - QR_m_c + QR_l_m - QR_m_p - QD_m_p
    )
    dT_pdt = (1 / (A_p * c_p)) * (
        QD_m_p + QV_i_p + QP_i_p - QR_p_f + QR_l_p - QR_p_v - QR_p_m
    )
    dT_c1dt = (1 / (rhod_c[1] * c_c[1] * l_c[1] * A_c)) * (QD_c12 - QD_c23)
    dT_c2dt = (1 / (rhod_c[2] * c_c[2] * l_c[2] * A_c)) * (QD_c23 - QD_c34)
    dT_c3dt = (1 / (rhod_c[3] * c_c[3] * l_c[3] * A_c)) * (QD_c34 - QD_c45)
    dT_c4dt = (1 / (rhod_c[4] * c_c[4] * l_c[4] * A_c)) * (QD_c45 - QD_c56)
    dT_c5dt = (1 / (rhod_c[5] * c_c[5] * l_c[5] * A_c)) * (QD_c56 - QD_c67)

    dC_wdt = (
        (1 / (V * H_fg)) * (QT_v_i - QP_i_c - QP_i_f - QP_i_m - QP_i_p)
        - MW_i_e
        + MW_cc_i
    )
    # dC_wdt = -MW_i_e

    return np.array(
        [
            dT_cdt,
            dT_idt,
            dT_vdt,
            dT_mdt,
            dT_pdt,
            dT_fdt,
            dT_c1dt,
            dT_c2dt,
            dT_c3dt,
            dT_c4dt,
            dT_c5dt,
            dC_wdt,
        ]
    )


def derivatives(
    h1, h2, numDays, paramsinput, ndp, filePathWeather, filePathWeatherForecast, LatestTimeHourValue
):

    # Get historical weather data
    clim_historical = np.transpose(climterp_linear(h1, h2, numDays, filePathWeather))
    # Get forecast weather data for the next two days
    clim_forecast = np.transpose( climterp_forecast_linear(numDays=2, filepath_weather_forecast=filePathWeatherForecast) )
    # Concatenate into single array - organised in ascending order of timestamp
    clim = np.concatenate((clim_historical, clim_forecast), axis=0)
    # Convert to pandas DataFrame
    clim = pd.DataFrame(clim, columns=["timestamp", "temperature", "relative_humidity"])
    # find duplicated timestamps. If two duplicated timestamps are found, keep historical over forecast
    is_duplicate = clim.duplicated("timestamp", keep="first")
    clim = clim[~is_duplicate]
    # drop the "timestamp" column
    clim = clim.drop("timestamp", axis=1)
    clim = clim.to_numpy()

    # Add extra weather if scenario evaluation

    # if switch1 == 1: # Testing scenario
    seconds_in_hour = 3600
    samples_in_hour = int(seconds_in_hour/deltaT)
    LastDayData = clim[
        -24 * samples_in_hour :,
    ]

    ## Create extended weather file
    extend_by_days = 1 # 2 days of forecasts plus 1 day of extension
    ExtendClimate = np.concatenate((clim,) + (LastDayData,) * extend_by_days)
    h2 = int(np.floor(ExtendClimate.shape[0]/samples_in_hour))

    climate = ExtendClimate

    NP = np.shape(paramsinput)[2]

    NOut = 1 + h2 - h1

    results = np.zeros((12, NOut, NP))

    # Loop over mean, upper quantile, lower quantile, and scenario.
    for i in range(NP):
        # tic = time.time()

        logging.info(i + 1)

        AirChangeHour = paramsinput[:, 0, i]
        IntAirSpeed = paramsinput[:, 1, i]
        ndh = paramsinput[:, 2, i]
        lshift = paramsinput[:, 3, i]

        # Initial conditions
        T_i_0 = 295
        T_c_0 = 293
        T_f_0 = 293
        T_v_0 = 297
        T_m_0 = 297
        T_p_0 = 297
        T_c1_0 = 295
        T_c2_0 = 292
        T_c3_0 = 291
        T_c4_0 = 289
        T_c5_0 = 287
        C_w_0 = 0.012

        z = [
            T_c_0,
            T_i_0,
            T_v_0,
            T_m_0,
            T_p_0,
            T_f_0,
            T_c1_0,
            T_c2_0,
            T_c3_0,
            T_c4_0,
            T_c5_0,
            C_w_0,
        ]

        daynum = [0]
        count = [0]

        ACH = AirChangeHour / 3600
        ias = IntAirSpeed

        t = [h1 * 3600, h2 * 3600]
        tval = np.linspace(h1 * 3600, h2 * 3600, NOut)

        params = [
            climate,
            ACH,
            ias,
            daynum,
            count,
            h1,
            h2,
            ndh,
            lshift,
            LatestTimeHourValue,
        ]

        output = solve_ivp(
            model, t, z, method="BDF", t_eval=tval, rtol=1e-5, args=params
        )

        results[:, :, i] = output.y

    return results


def priorPPF():
    u = np.random.uniform(0, 1, 3)
    # t1 = uniform.ppf(u[0], 1, 9)
    # t2 = uniform.ppf(u[1], 0.1, 1.0)
    # t3 = uniform.ppf(u[2], 0.1, 2.9)
    # t1 = gamma.ppf(u[0], 9.5, 1)
    # t2 = gamma.ppf(u[1], 6, 0.75)
    # t3 = gamma.ppf(u[2], 2.5, 0.5)
    # t1 = np.exp(norm.ppf(u[0], -0.8, 0.5)) #1.85, 0.2 gives mean around 8, 1, 0.3 gives mean around 3
    t1 = norm.ppf(u[0], 0.5, 0.15)
    # t2 = np.exp(norm.ppf(u[1], -0.8, 0.5)) #0.55, 0.45 gives mean around 2, 1.25, 0.05 gives mean of 3.5
    t2 = norm.ppf(u[1], 0.5, 0.15)
    # t3 = np.exp(norm.ppf(u[2], -0.2, 0.25)) #-0.8, 0.75 gives mean of 0.6, -1.5, 0.25 gives mean of 0.2
    # l = np.exp(norm.ppf(u[3], -1.5, 0.25))
    l = np.exp(norm.ppf(u[2], -1.5, 0.25))
    #
    #
    return np.array([t1, t2, l])
