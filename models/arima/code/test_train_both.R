library(lubridate)
library(dplyr)
library(forecast)
library(Metrics)

SECONDS.PERMINUTE = 60
MINS.PERHOUR = 60
HOURS.PERDAY = 24
SECONDS.PERDAY = HOURS.PERDAY * MINS.PERHOUR * SECONDS.PERMINUTE
SENSOR_ID = list(Temperature_FARM_16B1=18, Temperature_Farm_16B2=27, Temperature_Farm_16B4=23)
MEASURE_ID = list(Temperature_Mean = 1, Temperature_Upper = 2, Temperature_Lower = 3, Temperature_Median = 4)
MODEL_ID = list(ARIMA = 1, BSTS = 2)

source(paste0(".","/may_live_functions.R"), echo=FALSE)
source(paste0(".","/pushData.R"), echo=FALSE)

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
  oneDaysIntoPast = 1*SECONDS.PERDAY
  twoDaysIntoPast = 2*SECONDS.PERDAY
  threeDaysIntoPast = 3*SECONDS.PERDAY
  fourDaysIntoPast = 4*SECONDS.PERDAY
  list_f_timestamps = seq(from=latestTimeStamp-fourDaysIntoPast, to= latestTimeStamp-twoDaysIntoPast, by="2 days")
  #list_f_timestamps = seq(from=latestTimeStamp-threeDaysIntoPast, to= latestTimeStamp-oneDaysIntoPast, by="2 days")
  list_f_timestamps[length(list_f_timestamps)]
}

getOneYearDataUptoDate = function(observations, forecast_timestamp = ? Date) {
  # select one year
  oneYear = 365*SECONDS.PERDAY

  tobj0 = observations[t_ee$FarmTimestamp>=(forecast_timestamp-oneYear) & t_ee$FarmTimestamp <= (forecast_timestamp),]
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
  observationsForThisSensor
}

splitTrainingTestData = function (tobj, historicalDataStart, forecastDataStart) {
  daysIntoFuture = 2
  tsel = dplyr::filter(tobj, FarmTime >= (historicalDataStart) & FarmTime <= forecastDataStart)

  #fullcov <- constructCov(tsel$Lights, tsel$FarmTime)
  # indices for training
  trainsel = 1:(which(tsel$FarmTime==(forecastDataStart))-1)
  # indices for forecasting
  testsel = rep((which(tsel$FarmTime==(forecastDataStart))-24):(which(tsel$FarmTime==(forecastDataStart))-1),2)
  #

  list(tsel=tsel, trainSelIndex=trainsel, testSelIndex=testsel)
}

overrideTee = function(cleanedDataPath) {
  readRDS(cleanedDataPath)
}

getCurrentData = function(t_ee) {
  latest_timestamp = standardiseLatestTimestamp(max(t_ee$FarmTimestamp))
  forecast_timestamp = getForecastTimestamp(latest_timestamp)
  #forecast_timestamp = latest_timestamp - 1*SECONDS.PERDAY
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
    #model = (forecast::Arima(available.Data$Sensor_temp[trainIndex], xreg = NULL,
                             order = c(p,d,q),
                             seasonal = list(order=c(1,1,0),period=24),method = MINIMIZE_CONDITIONAL_SUM_OF_SQUARES))
  }

  forecastArima = function(available.Data, forecastIndex, arima.Model) {
    #print("Forecasting the Static model")
    numberOfHours=48 # was 16?
    results = forecast::forecast(arima.Model, xreg = available.Data$Lights[forecastIndex], h=numberOfHours)
    #results = forecast::forecast(arima.Model, xreg = NULL, h=numberOfHours)
    list(upper=results$upper, lower=results$lower, mean=results$mean)
  }

  runArimaPipeline = function(split.Data, sensorID) {
    model.arima = trainArima(available.Data=split.Data$tsel, trainIndex = split.Data$trainSelIndex)
    results.arima = forecastArima(available.Data=split.Data$tsel, forecastIndex=split.Data$testSelIndex, model.arima)
    #print(results.arima)
    stats.arima = sim_stats_arima(results.arima)

    records.mean.arima = list(measure_id = MEASURE_ID$Temperature_Mean, measure_values = results.arima$mean)
    records.upper.arima = list(measure_id = MEASURE_ID$Temperature_Upper, measure_values = results.arima$upper[,2])
    records.lower.arima = list(measure_id = MEASURE_ID$Temperature_Lower, measure_values = results.arima$lower[,2])
    records.arima = list(records.mean.arima, records.upper.arima, records.lower.arima)

    run.arima = list(sensor_id=sensorID, model_id=MODEL_ID$ARIMA, records=records.arima)

    return(run.arima)
    #writeRun(run.arima, time_forecast)

  }

  trainBSTS = function(available.Data, trainIndex) {
    numIterations = 1000 # default = 1000
    fullcov <- constructCov(available.Data$Lights[trainIndex], available.Data$FarmTime[trainIndex])
    mc = list()
    mc = bsts::AddLocalLevel(mc, y=available.Data$Sensor_temp[trainIndex])
    #mc_withRegression = try({
    #  bsts::AddDynamicRegression(mc, available.Data$Sensor_temp[trainIndex]~fullcov[trainIndex,-c(26)]) #remove the hour that usually happens before the lights are on
    #})
    #
    # Remove any zero columns
    zerocolumns = which(!apply(fullcov,2,sd) > 0)
    if (length(zerocolumns) == 0){
      fullcov_zero_removed = fullcov
     } else {
      fullcov_zero_removed = fullcov[,-zerocolumns]
     }
    #
    mc_withRegression = try({
      bsts::AddDynamicRegression(mc, available.Data$Sensor_temp[trainIndex]~fullcov_zero_removed[trainIndex,]) #remove the hour that usually happens before the lights are on
    })
    #
    #model=NULL
    #if (inherits(mc_withRegression, "try-error")){
    #  model = bsts::bsts(available.Data$Sensor_temp[trainIndex], mc, niter=numIterations) #iter 1000
    #  print("Ran with error")
    #}
    #else {
    model = bsts::bsts(available.Data$Sensor_temp[trainIndex], mc_withRegression, niter=numIterations) #iter 1000
    #  print("Ran with No errors")
    #}
    model
  }

  forecastBSTS = function(available.Data, forecastIndex, trainIndex, model) {
    newcovtyp = constructCovTyp(available.Data$FarmTime[forecastIndex])
    periodToForecast = 48 # default 48
    burnRate=200 # default 200
    # Identify zero columns in fullcov again for removal
    fullcov <- constructCov(available.Data$Lights[trainIndex], available.Data$FarmTime[trainIndex])
    zerocolumns = which(!apply(fullcov,2,sd) > 0)
    print(zerocolumns)
    if (length(zerocolumns) == 0){
      newcovtyp_zero_removed = newcovtyp
    } else {
      newcovtyp_zero_removed = newcovtyp[,-zerocolumns]
    }
    #
    predict(model, burn=burnRate, newdata=newcovtyp_zero_removed, periodToForecast) #burn 200
  }

  runbstsPipeline = function(split.Data, sensorID){
    model.bsts = trainBSTS(available.Data=split.Data$tsel, trainIndex = split.Data$trainSelIndex)
    results.bsts = forecastBSTS(available.Data=split.Data$tsel, forecastIndex = split.Data$testSelIndex, trainIndex = split.Data$trainSelIndex, model.bsts)
    print(results.bsts)
    stats.bsts = sim_stats_bsts(results.bsts)

    records.mean.bsts = list(measure_id = MEASURE_ID$Temperature_Mean, measure_values = results.bsts$mean)
    records.median.bsts = list(measure_id = MEASURE_ID$Temperature_Median, measure_values = results.bsts$median)
    records.bsts = list(records.mean.bsts, records.median.bsts)

    run.bsts = list(sensor_id=sensorID, model_id=MODEL_ID$BSTS, records=records.bsts)
    #writeRun(run.bsts)
    return(run.bsts)
  }

  test1 = runArimaPipeline(split.Data, sensorID=sensorID)
  test2 = runbstsPipeline(split.Data, sensorID=sensorID)

  abr = list(test1,test2)
  #abr = list(test1)

  return(abr)
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

#cleanedDataPath = "../data/t_ee.RDS"
#t_ee = overrideTee(cleanedDataPath)
#reportStats(t_ee, "Mel")

#cleanedDataPath = "../data/280921_60_t_ee.RDS"
#cleanedDataPath = "../data/280921_120_t_ee.RDS"
#cleanedDataPath = "../data/280921_170_t_ee.RDS"
#t_ee = readRDS(cleanedDataPath)
#reportStats(t_ee, "Today")

currentData = getCurrentData(t_ee)
reportStats(t_ee, "Today")

tobj_list = currentData$tobj_list
forecast_timestamp = currentData$forecast_timestamp

daysOfHistoryForTraining = 200
historicalDataStart = forecast_timestamp - daysOfHistoryForTraining*SECONDS.PERDAY
forecastDataStart = forecast_timestamp

runModelsForSensors = function(historicalDataStart, forecastDataStart) {

  arima_results = vector("list", length(tobj_list))
  bsts_results = vector("list", length(tobj_list))
  names(arima_results) = names(tobj_list)
  names(bsts_results) = names(tobj_list)
  #results = vector("list", length(MODEL_ID))
  results = list(arima_results,bsts_results)
  names(results) = names(MODEL_ID)
  for (tobj_name in names(tobj_list)){
    updateString = sprintf("Generating predictions for: %s on Date %s",tobj_name,forecastDataStart)
    print(updateString)
    tobj_mm <- tobj_list[[tobj_name]]
    split.Data = splitTrainingTestData(tobj_mm, historicalDataStart, forecastDataStart)
    #print(sprintf("SENSOR %s=%i", tobj_name, SENSOR_ID[[tobj_name]]))
    abr_out = setupModels(split.Data, sensorID=SENSOR_ID[[tobj_name]],forecastDataStart)
    results$ARIMA[[tobj_name]] = abr_out[[1]]
    results$BSTS[[tobj_name]] = abr_out[[2]]
  }
  return(results)
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

#daysOfPredictions = 7
#getDaysPrediction(daysOfPredictions, forecast_timestamp-(0*SECONDS.PERDAY))

ar = runModelsForSensors(historicalDataStart, forecastDataStart)

# Plot forecast and monitored data
tobj <- tobj_list[["Temperature_FARM_16B1"]]
#daysIntoFuture = 2
#tsel = dplyr::filter(tobj, FarmTime >= (historicalDataStart) & FarmTime <= (forecastDataStart+(daysIntoFuture*SECONDS.PERDAY)))
t1 = (which(t_ee$FarmTime==(forecastDataStart))):(which(t_ee$FarmTime==(forecastDataStart))+47)
t2 = (which(t_ee$FarmTime==(forecastDataStart))-48):(which(t_ee$FarmTime==(forecastDataStart))+47)
t3 = seq(from=forecastDataStart, to=forecastDataStart+2*SECONDS.PERDAY-1, by="1 hour")
#tt = t_ee$FarmTimestamp[t2]
tt = seq(from=forecastDataStart-2*SECONDS.PERDAY, to=forecastDataStart+2*SECONDS.PERDAY-1, by="1 hour")
#t3 = t_ee$FarmTimestamp[t1]

t2m = ar$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t2u = ar$ARIMA$Temperature_FARM_16B1$records[[2]]$measure_values
t2l = ar$ARIMA$Temperature_FARM_16B1$records[[3]]$measure_values

t2b = ar$BSTS$Temperature_FARM_16B1$records[[1]]$measure_values

plot(tt,t_ee$Temperature_FARM_16B1[t2], type = "l", col = "blue", main = "Temperature_FARM_16B1", ylim=c(15,30))
lines(t3,t2u,col = "red", lty = 3)
lines(t3,t2l,col = "red", lty = 3)
polygon(c(t3, rev(t3)), c(t2l, rev(t2u)), col = "mistyrose1", lty=0)
lines(tt,t_ee$Temperature_FARM_16B1[t2], col = "blue")
lines(t3,t2m,col = "red", lty = 2)
lines(t3,t2u,col = "red", lty = 3)
lines(t3,t2l,col = "red", lty = 3)
lines(t3,t2b,col = "darkmagenta", lty = 2)

legend("topleft",c("Monitored","ARIMA Forecast", "BSTS Forecast"), col=c("blue","red","darkmagenta"), lty=c(1,2,2), cex=0.8)

#
tobj <- tobj_list[["Temperature_Farm_16B2"]]
#tsel = dplyr::filter(tobj, FarmTime >= (historicalDataStart) & FarmTime <= (forecastDataStart+(daysIntoFuture*SECONDS.PERDAY)))
#t1 = (which(tsel$FarmTime==(forecastDataStart))):(which(tsel$FarmTime==(forecastDataStart))+47)
#t3 = tsel$FarmTime[t1]

t2m = ar$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t2u = ar$ARIMA$Temperature_Farm_16B2$records[[2]]$measure_values
t2l = ar$ARIMA$Temperature_Farm_16B2$records[[3]]$measure_values

t2b = ar$BSTS$Temperature_Farm_16B2$records[[1]]$measure_values

plot(tt,t_ee$Temperature_Farm_16B2[t2], type = "l", col = "blue", main = "Temperature_Farm_16B2", ylim=c(15,30))
lines(t3,t2u,col = "red", lty = 3)
lines(t3,t2l,col = "red", lty = 3)
polygon(c(t3, rev(t3)), c(t2l, rev(t2u)), col = "mistyrose1", lty=0)
lines(tt,t_ee$Temperature_Farm_16B2[t2], col = "blue")
lines(t3,t2m,col = "red", lty = 2)
lines(t3,t2u,col = "red", lty = 3)
lines(t3,t2l,col = "red", lty = 3)
lines(t3,t2b,col = "darkmagenta", lty = 2)

legend("topleft",c("Monitored","ARIMA Forecast", "BSTS Forecast"), col=c("blue","red","darkmagenta"), lty=c(1,2,2), cex=0.8)

#
tobj <- tobj_list[["Temperature_Farm_16B4"]]
#tsel = dplyr::filter(tobj, FarmTime >= (historicalDataStart) & FarmTime <= (forecastDataStart+(daysIntoFuture*SECONDS.PERDAY)))
#t1 = (which(tsel$FarmTime==(forecastDataStart))):(which(tsel$FarmTime==(forecastDataStart))+47)
#t3 = tsel$FarmTime[t1]

t2m = ar$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t2u = ar$ARIMA$Temperature_Farm_16B4$records[[2]]$measure_values
t2l = ar$ARIMA$Temperature_Farm_16B4$records[[3]]$measure_values

t2b = ar$BSTS$Temperature_Farm_16B4$records[[1]]$measure_values

plot(tt,t_ee$Temperature_Farm_16B4[t2], type = "l", col = "blue", main = "Temperature_Farm_16B4", ylim=c(15,30))
lines(t3,t2u,col = "red", lty = 3)
lines(t3,t2l,col = "red", lty = 3)
polygon(c(t3, rev(t3)), c(t2l, rev(t2u)), col = "mistyrose1", lty=0)
lines(tt,t_ee$Temperature_Farm_16B4[t2], col = "blue")
lines(t3,t2m,col = "red", lty = 2)
lines(t3,t2u,col = "red", lty = 3)
lines(t3,t2l,col = "red", lty = 3)
lines(t3,t2b,col = "darkmagenta", lty = 2)

legend("topleft",c("Monitored","ARIMA Forecast", "BSTS Forecast"), col=c("blue","red","darkmagenta"), lty=c(1,2,2), cex=0.8)

## Calculate Errors

data_actual_16B1 = t_ee$Temperature_FARM_16B1[t_ee$FarmTimestamp>=(forecast_timestamp) & t_ee$FarmTimestamp<(forecast_timestamp + 48*3600)]
data_actual_16B2 = t_ee$Temperature_Farm_16B2[t_ee$FarmTimestamp>=(forecast_timestamp) & t_ee$FarmTimestamp<(forecast_timestamp + 48*3600)]
data_actual_16B4 = t_ee$Temperature_Farm_16B4[t_ee$FarmTimestamp>=(forecast_timestamp) & t_ee$FarmTimestamp<(forecast_timestamp + 48*3600)]

arima_predicted_16B1 = ar$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
arima_predicted_16B2 = ar$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
arima_predicted_16B4 = ar$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values

bsts_predicted_16B1 = ar$BSTS$Temperature_FARM_16B1$records[[1]]$measure_values
bsts_predicted_16B2 = ar$BSTS$Temperature_Farm_16B2$records[[1]]$measure_values
bsts_predicted_16B4 = ar$BSTS$Temperature_Farm_16B4$records[[1]]$measure_values

rmse_a_16B1 = rmse(data_actual_16B1, arima_predicted_16B1)
rmse_a_16B2 = rmse(data_actual_16B2, arima_predicted_16B2)
rmse_a_16B4 = rmse(data_actual_16B4, arima_predicted_16B4)

rmse_b_16B1 = rmse(data_actual_16B1, bsts_predicted_16B1)
rmse_b_16B2 = rmse(data_actual_16B2, bsts_predicted_16B2)
rmse_b_16B4 = rmse(data_actual_16B4, bsts_predicted_16B4)

rmse_ab_16B1 = rmse(arima_predicted_16B1, bsts_predicted_16B1)
rmse_ab_16B2 = rmse(arima_predicted_16B2, bsts_predicted_16B2)
rmse_ab_16B4 = rmse(arima_predicted_16B4, bsts_predicted_16B4)

nmbe_a_16B1 = 1/48*sum((arima_predicted_16B1 - data_actual_16B1)/(data_actual_16B1))
nmbe_a_16B2 = 1/48*sum((arima_predicted_16B2 - data_actual_16B2)/(data_actual_16B2))
nmbe_a_16B4 = 1/48*sum((arima_predicted_16B4 - data_actual_16B4)/(data_actual_16B4))

nmbe_b_16B1 = 1/48*sum((bsts_predicted_16B1 - data_actual_16B1)/(data_actual_16B1))
nmbe_b_16B2 = 1/48*sum((bsts_predicted_16B2 - data_actual_16B2)/(data_actual_16B2))
nmbe_b_16B4 = 1/48*sum((bsts_predicted_16B4 - data_actual_16B4)/(data_actual_16B4))

nmbe_ab_16B1 = 1/48*sum((arima_predicted_16B1 - bsts_predicted_16B1)/(bsts_predicted_16B1))
nmbe_ab_16B2 = 1/48*sum((arima_predicted_16B2 - bsts_predicted_16B2)/(bsts_predicted_16B2))
nmbe_ab_16B4 = 1/48*sum((arima_predicted_16B4 - bsts_predicted_16B4)/(bsts_predicted_16B4))
