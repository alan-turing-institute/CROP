library(lubridate)
library(dplyr)
library(forecast)

source(paste0(".","/may_live_functions.R"), echo=FALSE)

SECONDS.PERMINUTE = 60
MINS.PERHOUR = 60
HOURS.PERDAY = 24
SECONDS.PERDAY = HOURS.PERDAY * MINS.PERHOUR * SECONDS.PERMINUTE
SENSOR_ID = list(Humidity_FARM_16B1=18, Humidity_Farm_16B2=27, Humidity_Farm_16B4=23)
MEASURE_ID = list(Humidity_Mean = 1, Humidity_Upper = 2, Humidity_Lower = 3, Humidity_Median = 4)

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
  list_f_timestamps = seq(from=latestTimeStamp-fourDaysIntoPast, to= latestTimeStamp-twoDaysIntoPast, by="2 days")
  list_f_timestamps[length(list_f_timestamps)]
}

standardiseObservations = function(observations, sensor =? string) {
  observationsForThisSensor = observations
  names(observationsForThisSensor)[tolower(names(observationsForThisSensor))==tolower(sensor)] = "Sensor_temp"
  observationsForThisSensor = observationsForThisSensor[,c("EnergyCP", "FarmTime", "Sensor_temp", "DateFarm")]
  observationsForThisSensor = fill_data(observationsForThisSensor)
  observationsForThisSensor
}

getOneYearDataUptoDate = function(observations, forecast_timestamp = ? Date) {
  # select one year
  oneYear = 365*SECONDS.PERDAY
  
  tobj0 = observations[t_ee$FarmTimestamp>=(forecast_timestamp-oneYear),]
  tobj0$FarmTime = tobj0$FarmTimestamp
  tobj0$DateFarm = as.Date(tobj0$FarmTimestamp) 
  
  #tobj0$EnergyCP <- ifelse(is.na(tobj0$EnergyCP),0,tobj0$EnergyCP*2)
  total_hourly_energy_consumption = 2
  tobj0$EnergyCP = tobj0$EnergyCP*total_hourly_energy_consumption
  
  tobj0
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

cleanedDataPath = "./t_ee_March282022.RDS"
t_ee = readRDS(cleanedDataPath) 

currentData = getCurrentData(t_ee)

tobj_list = currentData$tobj_list
forecast_timestamp = currentData$forecast_timestamp

daysOfHistoryForTraining = 200
historicalDataStart = forecast_timestamp - daysOfHistoryForTraining*SECONDS.PERDAY
forecastDataStart = forecast_timestamp

###
tobj_name = "Humidity_Farm_16B2"
tobj_mm <- tobj_list[[tobj_name]]

split.Data = splitTrainingTestData(tobj_mm, historicalDataStart, forecastDataStart)

available.Data=split.Data$tsel 
trainIndex = split.Data$trainSelIndex

p = 4 # AR order
d = 1 # degree of difference
q = 2 # MA order

MINIMIZE_CONDITIONAL_SUM_OF_SQUARES = "CSS"
model = (forecast::Arima(available.Data$Sensor_temp[trainIndex], xreg = NULL,
              order = c(p,d,q),
              seasonal = list(order=c(1,1,0),period=24),method = MINIMIZE_CONDITIONAL_SUM_OF_SQUARES))

foo <- fitted(model, xreg = NULL)

# Plot
par(mar = c(4.1, 4.4, 4.1, 1.9))
plot(available.Data$FarmTime,available.Data$Sensor_temp, type = "l", col = "black", 
     xlim = c(as.POSIXct('2022-02-24 00:00:00', format = "%Y-%m-%d %H:%M:%S"), 
              as.POSIXct('2022-03-28 23:00:00', format = "%Y-%m-%d %H:%M:%S")),
     xlab = "Date",
     ylab = expression(paste("Temperature ("^"o","C)")),
     main=c(tobj_name, "training days", daysOfHistoryForTraining))
lines(available.Data$FarmTime[trainIndex],foo, col = "blue", lty = 2)

numberOfHours=48
results = forecast::forecast(model, xreg = NULL, h=numberOfHours)

tt = seq(from=forecastDataStart-(0)*SECONDS.PERDAY, to=forecastDataStart+(2)*SECONDS.PERDAY-1, by="1 hour")
lines(tt,results$mean, col = "red", lty = 2)

leg_cols <- c("black", "blue", "red")
leg_lab <- c("data", "fitted", "forecast")

legend("topright", col = leg_cols, lty=c(1,2,2), 
       legend = leg_lab, bty = "n")

# Output to csv
xf = c(tobj_name,"_",daysOfHistoryForTraining,"_","fitted",".csv")
filename = paste(xf, collapse="")
results_fit = data.frame(available.Data$FarmTime[trainIndex],foo)
write.csv(results_fit,filename, row.names = FALSE)

xf = c(tobj_name,"_",daysOfHistoryForTraining,"_","forecast",".csv")
filename = paste(xf, collapse="")
results_forecast = data.frame(tt,results$mean,results$lower,results$upper)
write.csv(results_forecast,filename, row.names = FALSE)
