from TestScenarioV2 import FILEPATH_WEATHER
import functions_scenarioV1 as functions_scenario
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

filepath_data = 'C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/MonitoredV1.csv'
filepath_resultsRH = 'C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/resultsRHV1.csv'
filepath_resultsT = 'C:/Users/rmw61/Documents/CROP/versioning/Data_model/models/dynamic/data/resultsTV1.csv'

# Scenario

ventilation_rate:int=1
num_dehumidifiers:int=2
shift_lighting:int=-3
  
# Plot Results
header_list = ["DateTime", "T_e", "RH_e"]
ExternalWeather = pd.read_csv(FILEPATH_WEATHER, delimiter=',', names=header_list)
        
h2 = 240
h1 = h2-240
ind = h2-h1+1
ndp =int( (h2-h1)/3)

TWeather= ExternalWeather.T_e[-ind:].astype(np.float64) # +1 to ensure correct end point
RHWeather = ExternalWeather.RH_e[-ind:].astype(np.float64)

# Internal conditions
MonitoredData = pd.read_csv(filepath_data, parse_dates=True, header = None)
TData= MonitoredData[-ind:][1].astype(np.float64) # +1 to ensure correct end point
RHData = MonitoredData[-ind:][2].astype(np.float64)

p1 = int(h1) # start hour 
delta_h = 3 # hours between data points
p2 = int(ndp*delta_h+p1) # end data point 

sq = np.linspace(p1,p2,ndp+1,endpoint='true')
seq = sq.astype(np.int64)

t = np.linspace(h1-h2,3*24,1+240+3*24)
t1 = np.linspace(0,3*24,1+3*24)
td = np.linspace(h1-h2,0,81)

dpRH = RHData.iloc[seq]
dpT = TData.iloc[seq]+273.15
dpCw = dpRH/100 * functions_scenario.sat_conc(dpT)

# Read in results
T_air = pd.read_csv(filepath_resultsT, parse_dates=True, header = None)
RH_air = pd.read_csv(filepath_resultsRH, parse_dates=True, header = None)
  
#
fig = plt.figure()

ax1 = fig.add_subplot(1,2,1)
plt.plot(t,T_air[1]-273.15,'r')

ax1.fill_between(t[:-73], T_air[3][:-73]-273.15, T_air[4][:-73]-273.15, color='red', alpha = 0.2)
  
plt.plot(t1,T_air[2][-73:]-273.15,'b--')
plt.scatter(td,dpT-273.15, marker='.', color='k')
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
ax1.set_xlabel('Hour', fontsize=8)
ax1.set_ylabel('Temperature ($\mathregular{^{o}}$C)', fontsize=8)
ax1.set_title('Temperature', fontsize=10)
ax1.axvline(x=0, color='k')
ax1.set_xlim(-120, 72)

ax3 = fig.add_subplot(1,2,2)
lbl1 = str(int(ventilation_rate)) + ' ACH'
lbl2 = ', ' + str(int(num_dehumidifiers/2)) + ' DH'
lbl3 = ', ' + str(int(shift_lighting)) + ' hours'
plt.plot(t,100*RH_air[1],'r', label='BAU')
ax3.fill_between(t[:-73], 100*RH_air[3][:-73], 100*RH_air[4][:-73], color='red', alpha = 0.2)

plt.plot(t1,100*RH_air[2][-73:],'b--', label= lbl1 + lbl2 + lbl3)
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

TBAUstat = T_air[1][-73:]
TSEstat = T_air[2][-73:]

RHBAUstat = RH_air[1][-73:]
RHSEstat = RH_air[2][-73:]

testTBAU = TBAUstat>setTmax
testTBAU_low = TBAUstat<setTmin
testTSE = TSEstat>setTmax
testTSE_low = TSEstat<setTmin

testRHBAU = RHBAUstat>setRHmax
testRHBAU_low = RHBAUstat<setRHmin
testRHSE = RHSEstat>setRHmax
testRHSE_low = RHSEstat<setRHmin

  #y1 = ([np.sum(testTBAU), 72])
y1 = {'T<Tmin': np.sum(testTBAU_low), 'T OK': 73-np.sum(testTBAU)-np.sum(testTBAU_low), 'T>Tset': np.sum(testTBAU)}
names1 = [key for key,value in y1.items() if value!=0]
values1 = [value for value in y1.values() if value!=0]

  #y2 = ([np.sum(testTSE), 72])
  #y2 = {'T<Tset': 72-np.sum(testTSE), 'T>Tset': np.sum(testTSE)}
y2 = {'T<Tmin': np.sum(testTSE_low), 'T OK': 73-np.sum(testTSE)-np.sum(testTSE_low), 'T>Tset': np.sum(testTSE)}
names2 = [key for key,value in y2.items() if value!=0]
values2 = [value for value in y2.values() if value!=0]

  #y3 = ([np.sum(testRHBAU), 72])
  #y3 = {'RH<RHset': 72-np.sum(testRHBAU), 'RH>RHset': np.sum(testRHBAU)}
y3 = {'RH<RHmin': np.sum(testRHBAU_low), 'RH OK': 73-np.sum(testRHBAU)-np.sum(testRHBAU_low), 'RH>RHset': np.sum(testRHBAU)}
names3 = [key for key,value in y3.items()]
values3 = [value for value in y3.values()]

  #y4 = ([np.sum(testRHSE), 72])
  #y4 = {'RH<RHset': 72-np.sum(testRHSE), 'RH>RHset': np.sum(testRHSE)}
y4 = {'RH<RHmin': np.sum(testRHSE_low), 'RH OK': 73-np.sum(testRHSE)-np.sum(testRHSE_low), 'RH>RHset': np.sum(testRHSE)}
names4 = [key for key,value in y4.items()]
values4 = [value for value in y4.values()]

fig.savefig('ScenarioTHV1.png', format='png', dpi=1200, bbox_inches='tight')

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

fig2.savefig('ScenarioPieV1.png', format='png', dpi=1200, bbox_inches='tight')