SECONDS.PERMINUTE = 60
MINS.PERHOUR = 60
HOURS.PERDAY = 24
SECONDS.PERDAY = HOURS.PERDAY * MINS.PERHOUR * SECONDS.PERMINUTE
periodBetweenPredictions = SECONDS.PERDAY*7*4.3*4
historyLength = 200

date_Forecast_1 = as.POSIXct('2021-11-06 12:00:00', format="%Y-%m-%d %H:%M:%S", tz="UTC")
date_dataStarts_1 = date_Forecast_1-historyLength*SECONDS.PERDAY

date_Forecast_2 = date_Forecast_1 - (1*periodBetweenPredictions)
date_dataStarts_2 = date_Forecast_2-historyLength*SECONDS.PERDAY

date_Forecast_3 = date_Forecast_1 - (2*periodBetweenPredictions)
date_dataStarts_3 = date_Forecast_3-historyLength*SECONDS.PERDAY

date_Forecast_4 = date_Forecast_1 - (3*periodBetweenPredictions)
date_dataStarts_4 = date_Forecast_4-historyLength*SECONDS.PERDAY

date_Forecast = list(first=date_Forecast_1, second=date_Forecast_2, third=date_Forecast_3, fourth=date_Forecast_4) 
data_Starts = list(first=date_dataStarts_1, second=date_dataStarts_2, third=date_dataStarts_3, fourth=date_dataStarts_4) 

date_DataStarts = as.POSIXct('2020-04-27 12:00:00', format="%Y-%m-%d %H:%M:%S", tz="UTC")
date_DataEnds = as.POSIXct('2021-11-06 12:00:00', format="%Y-%m-%d %H:%M:%S", tz="UTC")

for (quarter in names(date_Forecast)){
  report = sprintf("%s forecast: %s\n data starts: %s\n\n",
                   quarter,
                   date_Forecast[[quarter]][1],
                   data_Starts[[quarter]][1])
  cat(report)
}

