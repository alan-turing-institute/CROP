
library(zoo)

report_print = function(report_Object) {
  report_Source = sprintf("Source: %s", report_Object$path)
  report_Dimension = sprintf("Dimension: [%s,%s]", dim(report_Object$object)[1],dim(report_Object$object)[2])
  report_Timestamps = sprintf("FarmTimestamp %s - %s", report_Object$object$FarmTimestamp[1], report_Object$object$FarmTimestamp[length(report_Object$object$FarmTimestamp)])
  report_TOC = c(report_Source,report_Dimension,report_Timestamps)
  
  for (content in report_TOC) {
    print(content)
  }
  print("")
}

path_208 = "../data/t_ee_208.RDS"
tee208 = list(path=path_208, object=readRDS(path_208))

path_398 = "../data/t_ee_398.RDS"
#tee308 = list(path=path_398, object=readRDS(path_398))

path_410 = "../data/t_ee_410.RDS"
#tee410 = list(path=path_410, object=readRDS(path_410))

report_Objects = list(tee208)

for (t_object in report_Objects) {
  report_print(t_object)
}
forecast = readRDS("../data/Forecast_2021-04-26_16h.RDS")
forecast_16B1 = forecast$Middle_16B1

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

daysToForecast = 0.66
dateOfForecast = as.POSIXct('2021-04-26 12:00:00', format="%Y-%m-%d %H:%M:%S", tz="UTC")
indexRange = getTimeStamps(tee208$object$FarmTimestamp, dateOfForecast, daysToForecast)
startForecastIndex = min(indexRange)
endForecastIndex = max(indexRange)
temperature=tee208$object$Temperature_FARM_16B1[startForecastIndex:endForecastIndex]
time=tee208$object$FarmTimestamp[startForecastIndex:endForecastIndex]
predictions=forecast_16B1[[1]]$mean
#print(time)
#print(temperature)
#print(predictions)

getRMSE = function (actual, predicted, timestamp) {
  rmse = vector()
  for (t in 1:length(actual)) {
    rmse = sqrt((actual[t]-predicted[t])*(actual[t]-predicted[t]))
    #report = sprintf("[%s]\t%s %s\n", timestamp[t], actual[t], predicted[t])
    report = sprintf("[%s]\t %s\n", timestamp[t], rmse)
    cat(report)
  }
}

getRMSE(temperature, predictions, time)


