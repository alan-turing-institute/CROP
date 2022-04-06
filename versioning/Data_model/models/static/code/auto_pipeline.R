WRITE_TO_DATABASE = TRUE
RUN_ARIMA = TRUE
RUN_BSTS = FALSE

library(lubridate)

date_Forecast = as.POSIXct(now(tz = "UTC"), format="%Y-%m-%d %H:%M:%S")
numDaysTraining = 200

source(paste0("~/CROP/versioning/Data_model/models/static/code/getData.R"), echo=FALSE)
source(paste0("~/CROP/versioning/Data_model/models/static/code/cleanData.R"), echo=FALSE)
source(paste0("~/CROP/versioning/Data_model/models/static/code/may_live_functions.R"), echo=FALSE)
source(paste0("~/CROP/versioning/Data_model/models/static/code/pushData.R"), echo=FALSE)
source(paste0("~/CROP/versioning/Data_model/models/static/code/train.R"), echo=TRUE)
