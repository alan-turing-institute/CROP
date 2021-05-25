#library("plyr")
#library("ggplot2")
library(lubridate)
library(bsts)
library(dplyr)
#library("reshape2")
library(forecast)
library(mlflow)
library(carrier)

SECONDS.PERMINUTE = 60
MINS.PERHOUR = 60
HOURS.PERDAY = 24
SECONDS.PERDAY = HOURS.PERDAY * MINS.PERHOUR * SECONDS.PERMINUTE

source(paste0(".","/may_live_functions.R"), echo=FALSE)

loadData = function(dataObjectPath) {
  readRDS("../../LatestData/may_t_ee.RDS") 
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
  tobj0$EnergyCP = tobj0$EnergyCP*2
  
  tobj0
}

standardiseObservations = function(observations, sensor =? string) {
  observationsForThisSensor = observations
  names(observationsForThisSensor)[tolower(names(observationsForThisSensor))==tolower(sensor)] = "Sensor_temp"
  observationsForThisSensor = observationsForThisSensor[,c("EnergyCP", "FarmTime", "Sensor_temp", "DateFarm")]
  observationsForThisSensor = fill_data(observationsForThisSensor)
}

splitTrainingTestData = function (tobj, historicalDataStart, forecastDataStart) {
  daysIntoFuture = 2
  tsel = dplyr::filter(tobj, FarmTime >= (historicalDataStart) & FarmTime <= (forecastDataStart+(daysIntoFuture*SECONDS.PERDAY)))
  
  # indices for training
  trainsel = 1:(which(tsel$FarmTime==(forecastDataStart))-1)
  # indices for forecasting
  testsel = rep((which(tsel$FarmTime==(forecastDataStart))-24):(which(tsel$FarmTime==(forecastDataStart))-1),2)
  
  list(tsel=tsel, trainSelIndex=trainsel, testSelIndex=testsel)
}

cleanedDataPath = "../../LatestData/may_t_ee.RDS"
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

daysOfHistoryForTraining = 3
historicalDataStart = forecast_timestamp - daysOfHistoryForTraining*SECONDS.PERDAY
forecastDataStart = forecast_timestamp
split.Data = splitTrainingTestData(tobj_mm, historicalDataStart, forecastDataStart)

trainArima = function(available.Data, trainIndex) {
  p = 4 # AR order
  d = 1 # degree of difference
  q = 2 # MA order
  
  MINIMIZE_CONDITIONAL_SUM_OF_SQUARES = "CSS"
  model = (forecast::Arima(available.Data$Sensor_temp[trainIndex], xreg =  available.Data$Lights[trainIndex],
                 order = c(p,d,q),
                 seasonal = list(order=c(1,1,0),period=24),method = MINIMIZE_CONDITIONAL_SUM_OF_SQUARES))
}

forecastArima = function(available.Data, forecastIndex, arima.Model) {
  print("Training the Static model")
  results = forecast::forecast(arima.Model,xreg = available.Data$Lights[forecastIndex], h=48)
  list(upper=results$upper, lower=results$lower, mean=results$mean)
}

#model = trainArima(available.Data=split.Data$tsel, trainIndex = split.Data$trainSelIndex)
#forecaster = crate (function (model, input, hour) { 
#  forecast::forecast(model, xreg=input, h = hour)
#})
#forecast = forecaster(model, split.Data$tsel$Lights[split.Data$testSelIndex], 48)

with(mlflow::mlflow_start_run(), {
  model = trainArima(available.Data=split.Data$tsel, trainIndex = split.Data$trainSelIndex)
  forecaster = crate (function (model, input, hour) { 
    forecast::forecast(model, xreg=input, h = hour)
  })
  forecast = forecaster(model, split.Data$tsel$Lights[split.Data$testSelIndex], 48)
  #results = forecastArima(available.Data=split.Data$tsel, forecastIndex = split.Data$testSelIndex, model)
  
  message("ARIMA (timestamp)=", forecastDataStart)
  message("RMSE: ", 2)
  
  mlflow_log_param("Historical Data", historicalDataStart)
  mlflow_log_param("Historical Days", daysOfHistoryForTraining)
  mlflow_log_param("Forecast Starts", forecastDataStart)
  mlflow_log_metric("RMSE", 2)
  
  mlflow_log_model(forecaster, "model")
})


trainBSTS = function(available.Data, trainIndex, forecastIndex) {
  fullcov <- constructCov(available.Data$Lights, available.Data$FarmTime)
  mc = list()
  mc = bsts::AddLocalLevel(mc, y=available.Data$Sensor_temp[trainIndex])
  mc = bsts::AddDynamicRegression(mc, available.Data$Sensor_temp[trainIndex]~fullcov[trainIndex,-c(26)]) #remove the hour that usually happens before the lights are on
  #this centres the mean towards the lower part of the day so the model is easier to explain
  dynamic_fit = bsts::bsts(available.Data$Sensor_temp[trainIndex], mc, niter=1000) #iter 1000
}

forecastBSTS = function(available.Data, trainIndex, forecastIndex) {
  newcovtyp <- constructCovTyp(tsel$FarmTime[testsel])
  predtyp <- predict(dynamic_fit, burn=200, newdata=newcovtyp[,-c(26)],48) #burn 200
  
}

#bsts.Model = trainBSTS(available.Data=split.Data$tsel, trainIndex = split.Data$trainSelIndex)
#bsts.Results = forecastBSTS(available.Data=split.Data$tsel, forecastIndex = split.Data$testSelIndex, arima.Model)

