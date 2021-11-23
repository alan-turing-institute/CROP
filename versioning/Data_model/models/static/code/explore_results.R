#forecast = readRDS("../data/Forecast_2021-04-26_16h.RDS")
#forecast_16B1 = forecast$Middle_16B1

getTimeStamps = function (t_object_timestamps, startDate, days){
  SECONDS.PERMINUTE = 60
  MINS.PERHOUR = 60
  HOURS.PERDAY = 24
  SECONDS.PERDAY = HOURS.PERDAY * MINS.PERHOUR * SECONDS.PERMINUTE
  endDate = startDate + (days*SECONDS.PERDAY)
  interval = lubridate::interval(startDate, endDate)
  indexRange = vector()
  indexOfT = 0
  for (t in t_object_timestamps) {
    indexOfT = indexOfT + 1
    dateToCheck = as_datetime(t)
    if (dateToCheck %within% interval) {
      indexRange = append(indexRange, indexOfT, after=length(indexRange))
    }
  }
  indexRange
}

getRMSE = function (actual, predicted, timestamp) {
  rmse = vector()
  for (t in 1:length(actual)) {
    rmse = sqrt((actual[t]-predicted[t])*(actual[t]-predicted[t]))
    #report = sprintf("[%s]\t%s %s\n", timestamp[t], actual[t], predicted[t])
    report = sprintf("[%s]\t %s\n", timestamp[t], rmse)
    cat(report)
  }
}

path_208 = "../data/t_ee_208.RDS"
tee208 = list(path=path_208, object=readRDS(path_208))

daysToForecast = 0.66
dateOfForecast = as.POSIXct('2021-04-26 12:00:00', format="%Y-%m-%d %H:%M:%S", tz="UTC")
indexRange = getTimeStamps(tee208$object$FarmTimestamp, dateOfForecast, daysToForecast)
startForecastIndex = min(indexRange)
endForecastIndex = max(indexRange)
temperature=tee208$object$Temperature_FARM_16B1[startForecastIndex:endForecastIndex]
time=tee208$object$FarmTimestamp[startForecastIndex:endForecastIndex]
predictions=forecast_16B1[[1]]$mean
getRMSE(temperature, predictions, time)