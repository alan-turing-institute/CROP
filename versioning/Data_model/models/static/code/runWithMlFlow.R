runWithMLFlow = function() {
  with(mlflow_start_run(), {
    horizon = mlflow_param("horizon", 12, "numeric")
    model = trainArima(available.Data=split.Data$tsel, trainIndex = split.Data$trainSelIndex)
    inputJSON = toJSON(structure(list(value=split.Data$tsel$Lights[split.Data$testSelIndex])))
    
    forecaster = crate (function (input) { 
      #
      #myInput = "{\"value\":[1,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1]}"
      #df = as.data.frame(rjson::fromJSON(myInput))
      #results = forecast::forecast(!!model, xreg=df$value, h = 12)
      #list(upper=results$upper, lower=results$lower, mean=results$mean)
      jsonObject = jsonlite::toJSON(input)
      rObject=jsonlite::fromJSON(jsonObject)
      df = as.data.frame(rObject)
      results = forecast::forecast(!!model, xreg=df$value, h = 12)
      list(upper=results$upper, lower=results$lower, mean=results$mean)
    }, model)
    #forecast = forecaster(split.Data$tsel$Lights[split.Data$testSelIndex], horizon)
    #forecast = forecaster(input)
    
    message("ARIMA (timestamp)=", forecastDataStart)
    message("Horizon=", horizon)
    
    mlflow_log_param("Historical Data", historicalDataStart)
    mlflow_log_param("Historical Days", daysOfHistoryForTraining)
    mlflow_log_param("Forecast Starts", forecastDataStart)
    mlflow_log_metric("RMSE", 2)
    
    mlflow_log_model(forecaster, "model")
  })
  
  #mlflow_end_run()
}