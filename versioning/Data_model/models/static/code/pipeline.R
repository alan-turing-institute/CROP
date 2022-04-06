WRITE_TO_DATABASE = FALSE
RUN_ARIMA = TRUE
RUN_BSTS = FALSE

library(lubridate)

date_Forecast = as.POSIXct(now(tz = "UTC"), format="%Y-%m-%d %H:%M:%S")
numDaysTraining = 200

source(paste0(".","/getData.R"), echo=FALSE)
source(paste0(".","/cleanData.R"), echo=FALSE)
source(paste0(".","/may_live_functions.R"), echo=FALSE)
source(paste0(".","/pushData.R"), echo=FALSE)
source(paste0(".","/test_train_arima.R"), echo=FALSE)
