WRITE_TO_DATABASE = TRUE
RUN_ARIMA = TRUE
RUN_BSTS = FALSE

library(lubridate)

setwd("C:/Users/rmw61/CROP/versioning/Data_model/models/static/code")

date_Forecast = as.POSIXct(now(tz = "UTC"), format="%Y-%m-%d %H:%M:%S")
numDaysTraining = 110

start_time <- Sys.time()

#source(paste0("./getData_zensie.R"), echo=FALSE)
#env_raw_z = env_raw
#energy_raw_z = energy_raw
source(paste0("./getData_aranet.R"), echo=FALSE)
#env_raw_a = env_raw
#energy_raw_a = energy_raw
#env_raw = rbind(env_raw_z,env_raw_a)
#energy_raw = rbind(energy_raw_z,energy_raw_a)
source(paste0("./cleanData.R"), echo=FALSE)
source(paste0("./may_live_functions.R"), echo=FALSE)
source(paste0("./pushData.R"), echo=FALSE)
source(paste0("./train.R"), echo=TRUE)

end_time <- Sys.time()