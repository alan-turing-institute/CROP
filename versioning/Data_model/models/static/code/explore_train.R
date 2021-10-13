library(lubridate)
library(dplyr)
library(forecast)
library(bsts)

SECONDS.PERMINUTE = 60
MINS.PERHOUR = 60
HOURS.PERDAY = 24
SECONDS.PERDAY = HOURS.PERDAY * MINS.PERHOUR * SECONDS.PERMINUTE
#SENSOR_ID = list(Temperature_FARM_16B1=18, Temperature_Farm_16B2=27, Temperature_Farm_16B4=23)
SENSOR_ID = list(Temperature_Farm_16B4=23)
MEASURE_ID = list(Temperature_Mean = 1, Temperature_Upper = 2, Temperature_Lower = 3, Temperature_Median = 4)
MODEL_ID = list(ARIMA = 1, BSTS = 2)

source(paste0(".","/may_live_functions.R"), echo=FALSE)
source(paste0(".","/pushData.R"), echo=FALSE)

standardiseLatestTimestamp = function (latestTimeStamp = ? Date) {
  # Identify time to forecast based on latest day
  if (hour(latestTimeStamp) > 16){
    as.POSIXct(paste0(as.Date(max(t_ee$FarmTimestamp))," ", 16,":00:00"), tz="UTC")
  } else if  (hour(latestTimeStamp)<=4){
    as.POSIXct(paste0(as.Date(max(t_ee$FarmTimestamp))-1," ", 16,":00:00"), tz="UTC")
  }else  {
    as.POSIXct(paste0(as.Date(max(t_ee$FarmTimestamp))," ", 4,":00:00"), tz="UTC")
  }
}

getForecastTimestamp = function(latestTimeStamp = ? Date) {
  twoDaysIntoPast = 2*SECONDS.PERDAY
  fourDaysIntoPast = 4*SECONDS.PERDAY
  list_f_timestamps = seq(from=latestTimeStamp-fourDaysIntoPast, to= latestTimeStamp-twoDaysIntoPast, by="2 days")
  print(list_f_timestamps)
  list_f_timestamps[length(list_f_timestamps)]
}

getOneYearDataUptoDate = function(observations, forecast_timestamp = ? Date) {
  # select one year
  oneYear = 365*SECONDS.PERDAY
  interval = lubridate::interval(forecast_timestamp-oneYear, forecast_timestamp)
  print(interval)
  tobj0 = observations[t_ee$FarmTimestamp %within% interval,]
  tobj0$FarmTime = tobj0$FarmTimestamp
  tobj0$DateFarm = as.Date(tobj0$FarmTimestamp) 
  print (sprintf("Forecast date %s", forecast_timestamp))
  print (sprintf("1 Year data runs from %s to %s", min(tobj0$FarmTime), max(tobj0$FarmTime)))
  #tobj0$EnergyCP <- ifelse(is.na(tobj0$EnergyCP),0,tobj0$EnergyCP*2)
  total_hourly_energy_consumption = 2
  tobj0$EnergyCP = tobj0$EnergyCP*total_hourly_energy_consumption
  
  tobj0
}

standardiseObservations = function(observations, sensor =? string) {
  observationsForThisSensor = observations
  names(observationsForThisSensor)[tolower(names(observationsForThisSensor))==tolower(sensor)] = "Sensor_temp"
  observationsForThisSensor = observationsForThisSensor[,c("EnergyCP", "FarmTime", "Sensor_temp", "DateFarm")]
  observationsForThisSensor = fill_data_mean(observationsForThisSensor)
  observationsForThisSensor
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

overrideTee = function(cleanedDataPath) {
  readRDS(cleanedDataPath) 
}

getCurrentData = function(t_ee) {
  latest_timestamp = standardiseLatestTimestamp(max(t_ee$FarmTimestamp))
  forecast_timestamp = getForecastTimestamp(latest_timestamp)
  tobj0 = getOneYearDataUptoDate(observations = t_ee, forecast_timestamp = forecast_timestamp)
  
  tobj_list = list()
  for (sensorName in names(SENSOR_ID)){
    if (sensorName %in% names(t_ee))
      tobj_list[[sensorName]] = standardiseObservations(tobj0,sensorName)
  }
  
  list(tobj_list=tobj_list, forecast_timestamp=forecast_timestamp)
}

getHistoricalData = function(t_ee, forecastDate) {
  print(sprintf("I want the forecast starting: %s", forecastDate))
  #latest_timestamp = standardiseLatestTimestamp(forecastDate)
  latest_timestamp = forecastDate
  print(sprintf("Latest Standardised: %s", latest_timestamp))
  #forecast_timestamp = getForecastTimestamp(latest_timestamp)
  forecast_timestamp = forecastDate
  print(sprintf("What does this have to do with anything: %s", forecast_timestamp))
  tobj0 = getOneYearDataUptoDate(observations = t_ee, forecast_timestamp = forecast_timestamp)
  tobj_list = list()
  for (sensorName in names(SENSOR_ID)){
    if (sensorName %in% names(t_ee))
      tobj_list[[sensorName]] = standardiseObservations(tobj0,sensorName)
  }
  
  list(tobj_list=tobj_list, forecast_timestamp=forecast_timestamp)
}

setupModels = function(split.Data, sensorID, time_forecast) {
  trainArima = function(available.Data, trainIndex) {
    p = 4 # AR order
    d = 1 # degree of difference
    q = 2 # MA order
    
    #print("Training the Static model")
    MINIMIZE_CONDITIONAL_SUM_OF_SQUARES = "CSS"
    model = (forecast::Arima(available.Data$Sensor_temp[trainIndex], xreg =  available.Data$Lights[trainIndex],
                             order = c(p,d,q),
                             seasonal = list(order=c(1,1,0),period=24),method = MINIMIZE_CONDITIONAL_SUM_OF_SQUARES))
  }
  
  forecastArima = function(available.Data, forecastIndex, arima.Model) {
    #print("Forecasting the Static model")
    numberOfHours=16
    results = forecast::forecast(arima.Model, xreg = available.Data$Lights[forecastIndex], h=numberOfHours)
    list(upper=results$upper, lower=results$lower, mean=results$mean)
  }
  
  runArimaPipeline = function(split.Data, sensorID) {
    model.arima = trainArima(available.Data=split.Data$tsel, trainIndex = split.Data$trainSelIndex)
    results.arima = forecastArima(available.Data=split.Data$tsel, forecastIndex=split.Data$testSelIndex, model.arima)
    print(split.Data$testSelIndex)
    rds.arima=sprintf("../data/arima_208.rds")
    saveRDS(results.arima,rds.arima)
    stats.arima = sim_stats_arima(results.arima)
    
    records.mean.arima = list(measure_id = MEASURE_ID$Temperature_Mean, measure_values = results.arima$mean)
    records.upper.arima = list(measure_id = MEASURE_ID$Temperature_Upper, measure_values = results.arima$upper[,2])
    records.lower.arima = list(measure_id = MEASURE_ID$Temperature_Lower, measure_values = results.arima$lower[,2])
    records.arima = list(records.mean.arima, records.upper.arima, records.lower.arima)
    
    run.arima = list(sensor_id=sensorID, model_id=MODEL_ID$ARIMA, records=records.arima)
    #writeRun(run.arima, time_forecast)
    
  }
  
  trainBSTS = function(available.Data, trainIndex) {
    numIterations = 500 # default = 1000
    fullcov <- constructCov(available.Data$Lights, available.Data$FarmTime)
    mc = list()
    mc = bsts::AddLocalLevel(mc, y=available.Data$Sensor_temp[trainIndex])
    mc_withRegression = try({
      bsts::AddDynamicRegression(mc, available.Data$Sensor_temp[trainIndex]~fullcov[trainIndex,-c(26)]) #remove the hour that usually happens before the lights are on
    })
    model=NULL
    if (inherits(mc_withRegression, "try-error")){
      model = bsts::bsts(available.Data$Sensor_temp[trainIndex], mc, niter=numIterations) #iter 1000
      print("Ran with error")
    }
    else {
      model = bsts::bsts(available.Data$Sensor_temp[trainIndex], mc_withRegression, niter=numIterations) #iter 1000
      print("Ran with No errors")
    }
    model
  }
  
  forecastBSTS = function(available.Data, forecastIndex, model) {
    newcovtyp = constructCovTyp(available.Data$FarmTime[forecastIndex])
    periodToForecast = 48 # default 48
    burnRate=200 # default 200
    predict(model, burn=burnRate, newdata=newcovtyp[,-c(26)],periodToForecast) #burn 200
  }
  
  runbstsPipeline = function(split.Data, sensorID){
    model.bsts = trainBSTS(available.Data=split.Data$tsel, trainIndex = split.Data$trainSelIndex)
    results.bsts = forecastBSTS(available.Data=split.Data$tsel, forecastIndex = split.Data$testSelIndex, model.bsts)
    stats.bsts = sim_stats_bsts(results.bsts)
    
    records.mean.bsts = list(measure_id = MEASURE_ID$Temperature_Mean, measure_values = results.bsts$mean)
    records.median.bsts = list(measure_id = MEASURE_ID$Temperature_Median, measure_values = results.bsts$median)
    records.bsts = list(records.mean.bsts, records.median.bsts)
    
    run.bsts = list(sensor_id=sensorID, model_id=MODEL_ID$BSTS, records=records.bsts)
    writeRun(run.bsts)
  }
  
  runArimaPipeline(split.Data, sensorID=sensorID)
  #runbstsPipeline(split.Data, sensorID=sensorID)
}

reportStats = function(a_t_ee, label="Source") {
  stats.timestamp.numNA.a_t_ee = sprintf("%s NumNA/Rows: %i/%i = %f \n", 
                                         label, 
                                         sum(is.na(a_t_ee$Timestamp)),
                                         length(a_t_ee$Timestamp), 
                                         sum(is.na(a_t_ee$Timestamp))/length(a_t_ee$Timestamp))
  cat(stats.timestamp.numNA.a_t_ee)
  
  if (label == "Today"){
    stats.temperature.numNA.a_t_ee = sprintf("%s Temperature NumNA/Rows: %i/%i = %f\n", 
                                             label,
                                             sum(is.na(a_t_ee$Temperature_FARM_16B1)),
                                             length(a_t_ee$Temperature_FARM_16B1),
                                             sum(is.na(a_t_ee$Temperature_FARM_16B1))/length(a_t_ee$Temperature_FARM_16B1))
    cat(stats.temperature.numNA.a_t_ee)
  }
  
  if (label == "Mel"){
    stats.temperature.numNA.a_t_ee = sprintf("%s Temperature NumNA/Rows: %i/%i = %f\n", 
                                             label,
                                             sum(is.na(a_t_ee$Temperature_Farm_16B2)),
                                             length(a_t_ee$Temperature_Farm_16B2),
                                             sum(is.na(a_t_ee$Temperature_Farm_16B2))/length(a_t_ee$Temperature_Farm_16B2))
    cat(stats.temperature.numNA.a_t_ee)
  }
  
  stats.energy.numNA.a_t_ee = sprintf("%s Energy NumNA/Rows: %i/%i = %f \n", 
                                      label,
                                      sum(is.na(a_t_ee$EnergyCP)),
                                      length(a_t_ee$EnergyCP),
                                      sum(is.na(a_t_ee$EnergyCP))/length(a_t_ee$EnergyCP))
  cat(stats.energy.numNA.a_t_ee)
}

runModelsForSensors = function(historicalDataStart, forecastDataStart) {
  for (tobj_name in names(tobj_list)){
    updateString = sprintf("Generating predictions for: %s on Date %s",tobj_name,forecastDataStart)
    print(updateString)
    tobj_mm <- tobj_list[[tobj_name]]
    split.Data = splitTrainingTestData(tobj_mm, historicalDataStart, forecastDataStart)
    #print(sprintf("SENSOR %s=%i", tobj_name, SENSOR_ID[[tobj_name]]))
    setupModels(split.Data, sensorID=SENSOR_ID[[tobj_name]],forecastDataStart)
  }
}

get_date_days_ago = function(numDays, today) {
  today = as.POSIXct(today)
  today - (numDays*SECONDS.PERDAY)
} 

getDaysPrediction = function(daysOfPredictions, forecast_timestamp) {
  get_date_days_ago = function(numDaysAgo, today) {
    today = as.POSIXct(today)
    dateDaysAgo = today - (numDaysAgo*SECONDS.PERDAY)
    dateDaysAgo
  } 
  
  for (d in 0:daysOfPredictions){
    temp_forecastDataStart = get_date_days_ago(numDaysAgo=d, forecast_timestamp)
    temp_historicalDataStart = temp_forecastDataStart - (daysOfHistoryForTraining*SECONDS.PERDAY) + (d*SECONDS.PERDAY)
    print(sprintf("Forecast for Date: %s Historical data starts:%s",temp_forecastDataStart,temp_historicalDataStart))
    runModelsForSensors(temp_historicalDataStart, temp_forecastDataStart)
  }
  
}

cleanedDataPath = "../data/t_ee_208.RDS"
t_ee = overrideTee(cleanedDataPath)
reportStats(t_ee, "T_ee_208")

#forecast_timestamp = as.POSIXct('2021-04-26 12:00:00', format="%Y-%m-%d %H:%M:%S", tz="UTC")
#currentData = getHistoricalData(t_ee, forecast_timestamp)
currentData = getCurrentData(t_ee)

tobj_list = currentData$tobj_list
forecast_timestamp = currentData$forecast_timestamp
daysOfHistoryForTraining = 200
historicalDataStart = forecast_timestamp - daysOfHistoryForTraining*SECONDS.PERDAY
forecastDataStart = forecast_timestamp

#tobj_mm = currentData$tobj_list$Temperature_FARM_16B1
#split.Data = splitTrainingTestData(tobj_mm, historicalDataStart, forecastDataStart)

runModelsForSensors(historicalDataStart, forecastDataStart)
rds.arima=sprintf("../data/arima_208.rds")
results.arima = readRDS(rds.arima)

#actual = currentData$tobj_list$Temperature_FARM_16B1$Sensor_temp[4801:4848]
#predicted = results.arima$mean
#timerange = currentData$tobj_list$Temperature_FARM_16B1$FarmTime[4801: 4848]
#getRMSE(actual, predicted, timerange)






