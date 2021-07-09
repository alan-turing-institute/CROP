library(lubridate)
library(dplyr)
library(forecast)
library(mlflow)
library(carrier)
library(jsonlite)
library(bsts)

SECONDS.PERMINUTE = 60
MINS.PERHOUR = 60
HOURS.PERDAY = 24
SECONDS.PERDAY = HOURS.PERDAY * MINS.PERHOUR * SECONDS.PERMINUTE
SENSOR_ID = list(Temperature_FARM_16B1=18, Temperature_FARM_16B2=27, Temperature_FARM_16B2=23)
MEASURE_ID = list(Temperature_Mean = 1, Temperature_Upper = 2, Temperature_Lower = 3, Temperature_Median = 4)
MODEL_ID = list(ARIMA = 1, BSTS = 2)

source(paste0(".","/may_live_functions.R"), echo=FALSE)
source(paste0(".","/pushData.R"), echo=FALSE)

loadData = function(dataObjectPath) {
  readRDS(dataObjectPath) 
}

standardiseLatestTimestamp = function (latestTimeStamp = ? Date) {
  # Identify time to forecast based on latest day
  if (hour(latestTimeStamp) > 16){
    as.POSIXct(paste0(as.Date(max(t_ee$FarmTimestamp))," ", 16,":00:00"), tz="GMT")
  } else if  (hour(latestTimeStamp)<=4){
    as.POSIXct(paste0(as.Date(max(t_ee$FarmTimestamp))-1," ", 16,":00:00"), tz="GMT")
  }else  {
    as.POSIXct(paste0(as.Date(max(t_ee$FarmTimestamp))," ", 4,":00:00"), tz="GMT")
  }
}

getForecastTimestamp = function(latestTimeStamp = ? Date) {
  twoDaysIntoPast = 2*SECONDS.PERDAY
  fourDaysIntoPast = 4*SECONDS.PERDAY
  list_f_timestamps = seq(from=latest_timestamp-fourDaysIntoPast, to= latest_timestamp-twoDaysIntoPast, by="2 days")
  list_f_timestamps[length(list_f_timestamps)]
}

getOneYearDataUptoDate = function(observations, forecast_timestamp = ? Date) {
  # select one year
  tobj0 = observations[t_ee$FarmTimestamp>=(forecast_timestamp-365*24*3600),]
  tobj0$FarmTime = tobj0$FarmTimestamp
  tobj0$DateFarm = as.Date(tobj0$FarmTimestamp)
  
  #tobj0$EnergyCP <- ifelse(is.na(tobj0$EnergyCP),0,tobj0$EnergyCP*2)
  total_hourly_energy_consumption = 2
  tobj0$EnergyCP = tobj0$EnergyCP*total_hourly_energy_consumption
  
  tobj0
}

standardiseObservations = function(observations, sensor =? string) {
  observationsForThisSensor = observations
  names(observationsForThisSensor)[tolower(names(observationsForThisSensor))==tolower(sensor)] = "Sensor_temp"
  observationsForThisSensor = observationsForThisSensor[,c("EnergyCP", "FarmTime", "Sensor_temp", "DateFarm")]
  observationsForThisSensor = fill_data(observationsForThisSensor)
}

splitTrainingTestData = function (tobj, historicalDataStart, forecastDataStart) {
  daysIntoFuture = 1
  tsel = dplyr::filter(tobj, FarmTime >= (historicalDataStart) & FarmTime <= (forecastDataStart+(daysIntoFuture*SECONDS.PERDAY)))
  
  #fullcov <- constructCov(tsel$Lights, tsel$FarmTime)
  # indices for training
  trainsel = 1:(which(tsel$FarmTime==(forecastDataStart))-1)
  # indices for forecasting
  testsel = rep((which(tsel$FarmTime==(forecastDataStart))-24):(which(tsel$FarmTime==(forecastDataStart))-1),2)
  
  list(tsel=tsel, trainSelIndex=trainsel, testSelIndex=testsel)
}

cleanedDataPath = "../../../LatestData/may_t_ee.RDS"
t_ee = loadData(cleanedDataPath) 
latest_timestamp = standardiseLatestTimestamp(max(t_ee$FarmTimestamp))
forecast_timestamp = getForecastTimestamp(latest_timestamp)
tobj0 = getOneYearDataUptoDate(observations = t_ee, forecast_timestamp = forecast_timestamp)

tobj1 = standardiseObservations(tobj0,"Temperature_FARM_16B1")
#tobj2 = standardiseObservations(tobj0,"Temperature_FARM_16B2")
#tobj3 = standardiseObservations(tobj0,"Temperature_FARM_16B4")

sensor_loc = c("Middle_16B1")
tobj_list = list(tobj1)
tobj_mm <- tobj_list[[1]]

# pre-allocate a list of length of nuymber of sensors
list_forecasts = vector("list", length(tobj_list))
names(list_forecasts) = sensor_loc

daysOfHistoryForTraining = 30
historicalDataStart = forecast_timestamp - daysOfHistoryForTraining*SECONDS.PERDAY
forecastDataStart = forecast_timestamp
split.Data = splitTrainingTestData(tobj_mm, historicalDataStart, forecastDataStart)

trainArima = function(available.Data, trainIndex) {
  p = 4 # AR order
  d = 1 # degree of difference
  q = 2 # MA order
  
  print("Training the Static model")
  MINIMIZE_CONDITIONAL_SUM_OF_SQUARES = "CSS"
  model = (forecast::Arima(available.Data$Sensor_temp[trainIndex], xreg =  available.Data$Lights[trainIndex],
                           order = c(p,d,q),
                           seasonal = list(order=c(1,1,0),period=24),method = MINIMIZE_CONDITIONAL_SUM_OF_SQUARES))
}

forecastArima = function(available.Data, forecastIndex, arima.Model) {
  print("Forecasting the Static model")
  numberOfHours=48
  results = forecast::forecast(arima.Model, xreg = available.Data$Lights[forecastIndex], h=numberOfHours)
  list(upper=results$upper, lower=results$lower, mean=results$mean)
}

source('~/Documents/workspace/CROP/versioning/Data_model/test_model/arima/pushData.R')

model.arima = trainArima(available.Data=split.Data$tsel, trainIndex = split.Data$trainSelIndex)
results.arima = forecastArima(available.Data=split.Data$tsel, forecastIndex=split.Data$testSelIndex, model.arima)
stats.arima = sim_stats_arima(results.arima)

records.mean.arima = list(measure_id = MEASURE_ID$Temperature_Mean, measure_values = results.arima$mean)
records.upper.arima = list(measure_id = MEASURE_ID$Temperature_Upper, measure_values = results.arima$upper)
records.lower.arima = list(measure_id = MEASURE_ID$Temperature_Lower, measure_values = results.arima$lower)
records.arima = list(records.mean.arima, records.upper.arima, records.lower.arima)

run.arima = list(sensor_id=SENSOR_ID$Temperature_FARM_16B1, model_id=MODEL_ID$ARIMA, records=records.arima)
writeRun(run.arima)

trainBSTS = function(available.Data, trainIndex) {
  fullcov <- constructCov(available.Data$Lights, available.Data$FarmTime)
  mc = list()
  mc = bsts::AddLocalLevel(mc, y=available.Data$Sensor_temp[trainIndex])
  mc = bsts::AddDynamicRegression(mc, available.Data$Sensor_temp[trainIndex]~fullcov[trainIndex,-c(26)]) #remove the hour that usually happens before the lights are on
  #this centres the mean towards the lower part of the day so the model is easier to explain
  numIterations = 500 # default = 1000
  model = bsts::bsts(available.Data$Sensor_temp[trainIndex], mc, niter=numIterations) #iter 1000
  return (model)
}
forecastBSTS = function(available.Data, forecastIndex, model) {
  newcovtyp = constructCovTyp(available.Data$FarmTime[forecastIndex])
  periodToForecast = 48 # default 48
  predict(model, burn=200, newdata=newcovtyp[,-c(26)],periodToForecast) #burn 200
}

model.bsts = trainBSTS(available.Data=split.Data$tsel, trainIndex = split.Data$trainSelIndex)
results.bsts = forecastBSTS(available.Data=split.Data$tsel, forecastIndex = split.Data$testSelIndex, model.bsts)
stats.bsts = sim_stats_bsts(results.bsts)

records.mean.bsts = list(measure_id = MEASURE_ID$Temperature_Mean, measure_values = results.bsts$mean)
records.median.bsts = list(measure_id = MEASURE_ID$Temperature_Median, measure_values = results.bsts$median)
records.bsts = list(records.mean.bsts, records.median.bsts)

run.bsts = list(sensor_id=SENSOR_ID$Temperature_FARM_16B1, model_id=MODEL_ID$BSTS, records=records.bsts)
writeRun(run.bsts)
