# -*- coding: utf-8 -*-
"""
Created on Mon Dec  6 11:43:14 2021

@author: rmw61
"""

from functions_RunModelV1 import derivatives, sat_conc
from parameters import ACH, ias
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY
import numpy as np
import pandas as pd

filepath_Weather = "C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/WeatherV1.csv"
filepath_Monitored = "C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/MonitoredV1.csv"
filepath_LastDataPoint = "C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/LastDataPointV1.csv"
filepath_ACH = "C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/ACH_outV1.csv"
filepath_IAS = "C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/IAS_outV1.csv"
filepath_Length = "C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/Length_outV1.csv"

# Import Weather Data
header_list = ["DateTime", "T_e", "RH_e"]
Weather = pd.read_csv(filepath_Weather, delimiter=",", names=header_list)

# Latest timestamp for weather and monitored data - hour (for lights)
Weather_hour = pd.DataFrame(Weather, columns=["DateTime", "T_e", "RH_e"]).set_index(
    "DateTime"
)
LatestTime = Weather_hour[-1:]
LatestTimeHourValue = pd.DatetimeIndex(LatestTime.index).hour.astype(float)[0]

# Import DataPoints
LastDataPoint: np.ndarray = np.genfromtxt(filepath_LastDataPoint, delimiter=",")
ndp = np.size(LastDataPoint, 0)

# Import Calibrated ACH, IAS, Length
ACHinp: np.ndarray = np.genfromtxt(filepath_ACH, delimiter=",")
IASinp: np.ndarray = np.genfromtxt(filepath_IAS, delimiter=",")
Lengthinp: np.ndarray = np.genfromtxt(filepath_Length, delimiter=",")

ACHcal: float = ACHinp[1:, -1 * ndp :] * 9.0 + 1.0
ACHmean = np.mean(ACHcal, 0)
ACHuq = np.quantile(ACHcal, 0.95, 0)
ACHlq = np.quantile(ACHcal, 0.05, 0)

IAScal: float = IASinp[1:, -1 * ndp :] * 0.75 + 0.1
IASmean = np.mean(IAScal, 0)
IASuq = np.quantile(IAScal, 0.95, 0)
IASlq = np.quantile(IAScal, 0.05, 0)

Lengthcal: float = Lengthinp[1:, -1 * ndp :]
Lengthmean = np.mean(Lengthcal, 0)
Lengthuq = np.quantile(Lengthcal, 0.95, 0)
Lengthlq = np.quantile(Lengthcal, 0.05, 0)

# Set up input parameters (time varying ACH, IAS)

Parameters: np.ndarray = np.zeros((ndp + 1, 2, 3))

Parameters[0, 0, 0] = ACH
Parameters[0, 1, 0] = ias
Parameters[1 : ndp + 1, 0, 0] = ACHmean
Parameters[1 : ndp + 1, 1, 0] = IASmean

Parameters[0, 0, 1] = ACH
Parameters[0, 1, 1] = ias
Parameters[1 : ndp + 1, 0, 1] = ACHuq
Parameters[1 : ndp + 1, 1, 1] = IASlq

Parameters[0, 0, 2] = ACH
Parameters[0, 1, 2] = ias
Parameters[1 : ndp + 1, 0, 2] = ACHlq
Parameters[1 : ndp + 1, 1, 2] = IASuq

# Run model
h1 = 0
h2 = np.size(Weather, 0)

results = derivatives(h1, h2, Parameters, ndp, Weather, LatestTimeHourValue)

# Plot Results

T_air_mean = results[1, :, 0]
Cw_air_mean = results[11, :, 0]
RH_air_mean = Cw_air_mean / sat_conc(T_air_mean)

T_air_lq = results[1, :, 1]
Cw_air_lq = results[11, :, 1]
RH_air_lq = Cw_air_lq / sat_conc(T_air_lq)

T_air_uq = results[1, :, 2]
Cw_air_uq = results[11, :, 2]
RH_air_uq = Cw_air_uq / sat_conc(T_air_uq)

# Import Monitored Data
header_list = ["DateTime", "T_i", "RH_i"]
Monitored = pd.read_csv(filepath_Monitored, delimiter=",", names=header_list)
header_list = ["DateTime", "RH_i"]
DataPoint = pd.read_csv(filepath_LastDataPoint, delimiter=",", names=header_list)

# Plot predicted temperature, rh

fig = plt.figure()

ax1 = fig.add_subplot(2, 1, 1)
tt = Weather.DateTime
df = Weather
df["DateTime"] = pd.to_datetime(Weather["DateTime"])
dates = df["DateTime"]
ax1.fill_between(dates, T_air_uq - 273.15, T_air_lq - 273.15, color="r", alpha=0.2)
plt.plot(dates, T_air_mean - 273.15, "r")
# plt.plot(dates,T_air_uq-273.15,'r:')
# plt.plot(dates,T_air_lq-273.15,'r:')

plt.plot(dates, Weather.T_e, "k:")
plt.scatter(dates, Monitored.T_i, marker=".", color="k")
ax1.axes.get_xaxis().set_ticks([])
plt.ylabel("Temperature (degC)")

ax1 = fig.add_subplot(2, 1, 2)
ax1.fill_between(dates, RH_air_uq, RH_air_lq, color="r", alpha=0.2)
plt.plot(dates, RH_air_mean, "r")
# plt.plot(dates,RH_air_uq,'r:')
# plt.plot(dates,RH_air_lq,'r:')
plt.plot(dates, Weather.RH_e / 100, "k:")
plt.scatter(dates, Monitored.RH_i / 100, marker=".", color="k")

tt_d = DataPoint.DateTime
plt.scatter(tt_d, DataPoint.RH_i, marker="+", color="b")
plt.ylabel("RH")
plt.xticks(rotation=45)

fig.savefig("ModelRun.png", format="png", dpi=1200, bbox_inches="tight")

# Plot ACH, IAS
fig = plt.figure()

ax1 = fig.add_subplot(3, 1, 1)
plt.plot(tt_d, ACHmean, color="r")
ax1.fill_between(tt_d, ACHuq, ACHlq, color="r", alpha=0.2)
ax1.axes.get_xaxis().set_ticks([])
plt.ylabel("ACH")

ax2 = fig.add_subplot(3, 1, 2)
plt.plot(tt_d, IASmean, color="r")
ax2.fill_between(tt_d, IASuq, IASlq, color="r", alpha=0.2)
ax2.axes.get_xaxis().set_ticks([])
plt.ylabel("IAS")

ax3 = fig.add_subplot(3, 1, 3)
plt.plot(tt_d, Lengthmean, color="r")
ax3.fill_between(tt_d, Lengthuq, Lengthlq, color="r", alpha=0.2)
plt.xticks(rotation=90)
plt.ylabel("Length")

fig.savefig("ParameterValues.png", format="png", dpi=1200, bbox_inches="tight")
