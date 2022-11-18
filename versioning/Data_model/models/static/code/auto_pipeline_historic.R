WRITE_TO_DATABASE = FALSE
RUN_ARIMA = TRUE
RUN_BSTS = FALSE

library(lubridate)

setwd("C:/Users/rmw61/CROP/versioning/Data_model/models/static/code")

#date_Forecast = as.POSIXct(now(tz = "UTC"), format="%Y-%m-%d %H:%M:%S")
date_Forecast = as.POSIXct('2021-08-05 12:00:00', format="%Y-%m-%d %H:%M:%S", tz="UTC")
#date_Forecast = as.POSIXct(now(tz = "UTC"), format="%Y-%m-%d %H:%M:%S")
numDaysTraining = 300

start_time <- Sys.time()

source(paste0("./getData.R"), echo=FALSE)
source(paste0("./cleanData.R"), echo=FALSE)
#saveRDS(t_ee,file = "t_ee_March282022.rds")
saveRDS(t_ee,file = "t_ee_August052021.rds")
#source(paste0("./may_live_functions.R"), echo=FALSE)
#source(paste0("./pushData.R"), echo=FALSE)
#source(paste0("./train.R"), echo=TRUE)

end_time <- Sys.time()