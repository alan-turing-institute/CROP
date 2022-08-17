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
