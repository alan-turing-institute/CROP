# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from functions_scenario import derivatives, sat_conc
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pandas import DataFrame

# Start hour h2 is for test only - in live version will be current time
h2 = 1095
h1 = h2-240 # select previous 10 days
ndp = int((h2-h1)/12) # number of data points used for calibration

# Input calibrated parameters output from calibration model
# Stored in database? Currently output to csv file

ACHinp = np.genfromtxt('ACH_out.csv', delimiter=',')
IASinp = np.genfromtxt('IAS_out.csv', delimiter=',')

# Calculate mean calibrated ACH, IAS and 5%, 95% quantiles

ACHcal = ACHinp[1:,-1*ndp:]*9+1 # selects ACH values corresponding to the last ndp data points
ACHmean = np.mean(ACHcal,0)
ACHuq = np.quantile(ACHcal,0.95,0)
ACHlq = np.quantile(ACHcal,0.05,0)

IAScal = IASinp[1:,-1*ndp:]*0.75+0.1
IASmean = np.mean(IAScal,0)
IASuq = np.quantile(IAScal,0.95,0)
IASlq = np.quantile(IAScal,0.05,0)

# Set up parameters for runs: 1) BAU mean, 2) Scenario, 3) BAU UQ, 4) BAU LQ
# Scenario values N, ndh and lshift will come from sliders on dashboard

test = np.zeros((ndp,4,4))
#for i in range(np.size(test,2)):
test[:,0,0] = ACHmean
test[:,1,0] = IASmean
test[:,2,0] = 1
test[:,3,0] = 0

test[:,0,1] = ACHmean
test[:,1,1] = IASmean
test[:,2,1] = 1
test[:,3,1] = 0

test[:,0,2] = ACHuq
test[:,1,2] = IASlq
test[:,2,2] = 1
test[:,3,2] = 0

test[:,0,3] = ACHlq
test[:,1,3] = IASuq
test[:,2,3] = 1
test[:,3,3] = 0

# Scenario 1 - vary ACH
N = 1 # ventilation rate inout from slider

ScenEval = np.zeros((8,4,4))
ScenEval[:,0,0] = ACHmean[-1]
ScenEval[:,0,1] = N # input from slider
ScenEval[:,0,2] = ACHuq[-1]
ScenEval[:,0,3] = ACHlq[-1]

ScenEval[:,1,0] = IASmean[-1]
ScenEval[:,1,1] = IASmean[-1]
ScenEval[:,1,2] = IASlq[-1]
ScenEval[:,1,3] = IASuq[-1]

# Scenario 2 - vary number of dehumidifiers
ndh = 2 # number of dehumidifiers 

ScenEval[:,2,0] = 1
ScenEval[:,2,1] = ndh/2 # ndh input from slider (integer) (/2 as half farm modelled)
ScenEval[:,2,2] = 1
ScenEval[:,2,3] = 1

# Scenario 3 - shift lighting schedule (+/-hours)
lshift = -3

ScenEval[:,3,0] = 1
ScenEval[:,3,1] = lshift # lshift input from slider 
ScenEval[:,3,2] = 1
ScenEval[:,3,3] = 1

params = np.concatenate((test, ScenEval)) # put scenario on the end of the calibrated parameters

## Run model, using time varying ACH, IAS corresponding to outputs from calibration for 
#  first 10 days, then scenario evaluation values for last 3 days

results = derivatives(h1, h2, params, ndp) 
    
T_air = results[1,:,:]
Cw_air = results[11,:,:]
RH_air = Cw_air/sat_conc(T_air)

## Plot Results

p1 = h1 # start hour 
delta_h = 12 # hours between data points
p2 = ndp*delta_h+p1 # end data point 

seq = np.linspace(p1,p2,ndp+1,endpoint='true')

date_cols = ["DateTimex"]
Data = pd.read_csv("TRHE2018.csv", parse_dates=date_cols)
RHData =Data['MidFarmRH2']
TData =Data['MidFarmT']
    
#t = np.linspace(h1,h2+3*24,1+240+3*24)
t = np.linspace(h1-h2,3*24,1+240+3*24)
t1 = np.linspace(0,3*24,1+3*24)
td = np.linspace(h1-h2,0,21)

dpRH = RHData[seq]
dpT = TData[seq]+273.15
dpCw = dpRH/100 * sat_conc(dpT)

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
lbl1 = str(int(N)) + ' ACH'
lbl2 = ', ' + str(int(ndh)) + ' DH'
lbl3 = ', ' + str(int(lshift)) + ' hours'
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