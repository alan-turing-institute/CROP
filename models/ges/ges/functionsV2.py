# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 09:18:07 2021

@author: rmw61
"""
import logging
import numpy as np
import pandas as pd
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
from .parameters import ndh
from scipy.integrate import solve_ivp
from pathlib import Path

from inversion import *
from cropcore.model_data_access import get_days_weather
from .config import config

path_conf = config(section="paths")
cal_conf = config(section="calibration")

lighting_factor = float(cal_conf["lighting_factor"])


def climterp_linear(h1, h2, ExternalWeather):
    temp_in = None
    rh_in = None
    # if (filepath_weather):
    #    ExternalWeather = np.genfromtxt(filepath_weather, delimiter=',')
    #    temp_in = ExternalWeather[h1:h2+1,1] # +1 to ensure correct end point
    #    rh_in = ExternalWeather[h1:h2+1,2] # +1 to ensure correct end point
    # else:
    #    ExternalWeather = np.asarray(get_days_weather(numDays, numRows=numDays*24))
    #    temp_in = ExternalWeather[h1:h2+1,1].astype(np.float64) # +1 to ensure correct end point
    #    rh_in = ExternalWeather[h1:h2+1,2].astype(np.float64) # +1 to ensure correct end point

    temp_in = (
        ExternalWeather.T_e[h1 : h2 + 1]
    ).to_numpy()  # +1 to ensure correct end point
    rh_in = (
        ExternalWeather.RH_e[h1 : h2 + 1]
    ).to_numpy()  # +1 to ensure correct end point

    # # remove nans
    nans, x = nan_helper(temp_in)
    temp_in[nans] = np.interp(x(nans), x(~nans), temp_in[~nans])

    nans, x = nan_helper(rh_in)
    rh_in[nans] = np.interp(x(nans), x(~nans), rh_in[~nans])

    t = np.linspace(0, 864000 - 3600, (h2 - h1 + 1))  # 864000 = 240 hours i.e. 10 days
    deltaT = 600  # 10 minutes
    mult = np.linspace(0, 864000, int(1 + 864000 / deltaT))
    # logging.info("t: {0}, mult:{1}, input:{2}".format(t.shape,mult.shape,temp_in.shape))

    # ind = h2-h1+1

    # clim_t = np.interp(mult,t,temp_in[-ind:])
    # clim_rh = np.interp(mult,t,rh_in[-ind:])
    logging.info(f"Interpolating temperature {len(t)} {len(temp_in)}")
    clim_t = np.interp(mult, t, temp_in)
    clim_rh = np.interp(mult, t, rh_in)

    climate = np.vstack((clim_t, clim_rh))

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


def sat_conc(T):

    TC = T - T_k
    spec_hum = np.exp(11.56 - 4030 / (TC + 235))
    air_dens = -0.0046 * TC + 1.2978
    a = spec_hum * air_dens

    return a


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


def model(t, z, climate, ACHvec, iasvec, daynum, h1, h2, LatestTimeHourValue):

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

    n = int(np.floor((t - t_init) / deltaT))  # previously ceil?
    T_ext = climate[n, 0] + T_k
    RH_e = climate[n, 1] / 100
    Cw_ext = RH_e * sat_conc(T_ext)

    daynum.append(day(t))

    ## Set ACH,ias
    hour = np.floor(t / 3600)  # + 1?

    ACH = ACHvec
    ias = iasvec

    ## Lights
    day_hour = (
        (hour + LatestTimeHourValue) / 24 - np.floor((hour + LatestTimeHourValue) / 24)
    ) * 24
    L_on = (day_hour > -0.01 and day_hour < 08.01) or day_hour > 15.01
    AL_on = day_hour > 08.01 and day_hour < 16.01

    T_l = L_on * T_al + (1 - L_on) * T_i

    QV_l_i = f_heat * P_al * lighting_factor * L_on + P_ambient_al * AL_on + ndh * P_dh

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
    QS_int = f_light * P_al * lighting_factor * L_on / A_p

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


def derivatives(h1, h2, paramsinput, Weather, LatestTimeHourValue):
    """
    Parameters:
    ===========
    h1: int
    h2: int
    Weather: pandas DataFrame
    """

    logging.info(
        f"In derivatives, NP: {np.shape(paramsinput)[0]} h1:{h1} h2:{h2} len(Weather):{len(Weather)}"
    )
    # Get weather data
    climate = np.transpose(climterp_linear(h1, h2, Weather))

    # Get parameter values

    NP = np.shape(paramsinput)[0]

    NOut = 2

    results = np.zeros((12, NOut, NP))

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
    # count = [0]

    t = [h1 * 3600, h2 * 3600]
    tval = np.linspace(h1 * 3600, h2 * 3600, NOut)

    for i in range(NP):
        logging.info(
            f"in derivatives, step {i + 1} LatestTimeHourValue is {LatestTimeHourValue} "
        )
        AirChangeHour = paramsinput[i, 0]
        IntAirSpeed = paramsinput[i, 1]
        ACH = AirChangeHour / 3600
        ias = IntAirSpeed
        params = [climate, ACH, ias, daynum, h1, h2, LatestTimeHourValue]
        output = solve_ivp(
            model, t, z, method="BDF", t_eval=tval, rtol=1e-5, args=params
        )
        results[:, :, i] = output.y
    return results


def loadDistributions():
    # if (filePath_ACH and filePath_IAS and filePath_Length):
    #     df_ACH = pd.read_csv(filePath_ACH)
    #     df_IAS = pd.read_csv(filePath_IAS)
    #     df_Length = pd.read_csv(filePath_Length)
    # else:
    data_dir = Path(path_conf["data_dir"])
    filepath_ACH = data_dir / path_conf["filename_ach"]
    filepath_IAS = data_dir / path_conf["filename_ias"]
    filepath_Length = data_dir / path_conf["filename_length"]

    try:
        df_ACH = pd.read_csv(filepath_ACH)
    except FileNotFoundError:
        df_ACH = pd.DataFrame()
    try:
        df_IAS = pd.read_csv(filepath_IAS)
    except FileNotFoundError:
        df_IAS = pd.DataFrame()
    try:
        df_Length = pd.read_csv(filepath_Length)
    except FileNotFoundError:
        df_Length = pd.DataFrame()
    return df_ACH, df_IAS, df_Length


def priorPPF():
    df_ACH, df_IAS, df_Length = loadDistributions()
    nparticles = np.size(df_ACH, 0)
    jj = np.size(df_ACH, 1)
    if jj > 1:
        a_t1 = np.array(df_ACH.iloc[:, -1])
        a_t2 = np.array(df_IAS.iloc[:, -1])
        a_l = np.array(df_Length.iloc[:, -1])

        idx = np.random.randint(0, nparticles, size=1)

        # Include re-juvenation

        t1 = a_t1[idx][0] + np.random.normal(0, 0.05)
        t2 = a_t2[idx][0] + np.random.normal(0, 0.05)
        l = np.exp(np.log(a_l[idx][0]) + np.random.normal(0, 0.05))

    else:
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
