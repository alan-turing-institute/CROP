WRITE_TO_DATABASE = TRUE
RUN_ARIMA = TRUE
RUN_BSTS = TRUE

date_Forecast = as.POSIXct('2021-11-08 12:00:00', format="%Y-%m-%d %H:%M:%S", tz="UTC")
numDaysTraining = 300

source(paste0(".","/getData.R"), echo=FALSE)
source(paste0(".","/cleanData.R"), echo=FALSE)
source(paste0(".","/may_live_functions.R"), echo=FALSE)
source(paste0(".","/pushData.R"), echo=FALSE)
source(paste0(".","/train.R"), echo=FALSE)