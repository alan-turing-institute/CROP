# This script contains all the info to run the basic model
# 




## Set up ==========

# Load required packages
library(plyr)
library(ggplot2)
library(lubridate)
library(bsts)
require(dplyr)
require(reshape2)
require(forecast)

# Set folder
getwd()
motherfolder <- "C:/Users/mkj32/OneDrive - UIS/GU/Models_Live"

daughterfolder <-paste0(motherfolder,"/","Data_model") # 34 prediction dates, 17 models

setwd(daughterfolder)

## Load model


## Load data ------------
# This code loads the data from the LatestData folder, and finds the average hourly values
data_folder <-  paste0(motherfolder,"/","LatestData")
setwd(data_folder)
# Load raw from Python (API)
env_raw <- read.csv("Env_30MHz_raw.csv")
energy_raw <- read.csv("Energy_raw.csv")
# Make a timestamp column where the time format is unequivocally in UTC
energy_raw$Timestamp2 <- as.POSIXct(energy_raw$timestamp,tz="UTC")
env_raw$Timestamp2 <- as.POSIXct(env_raw$timestamp,tz="UTC")

# clean the data
source(paste0(daughter_folder,"/may_cleandata.R"), echo=FALSE)

# the average hourly temperature and humidity are returned in trh_api.RDS, data frame name all_sensors_df2
# the average hourly energy is returned in e_api.RDS, data frame ecp_api

# NB. More checks need to be made on the alignment between temperature and energy data as there are some inconsistencies with the latest downloaded data.

# the combined cleaned data frame is saved as t_ee.RDS

## Running the model --------------

# Identify time to forecast based on latest day

if (hour(max(t_ee$FarmTimestamp))>16){
  forecast_timestamp <- as.POSIXct(paste0(as.Date(max(t_ee$FarmTimestamp))," ", 16,":00:00"), tz="GMT")
} else if  (hour(max(t_ee$FarmTimestamp))<=4) {
  forecast_timestamp <- as.POSIXct(paste0(as.Date(max(t_ee$FarmTimestamp))-1," ", 16,":00:00"), tz="GMT")

}else  {
  forecast_timestamp <- as.POSIXct(paste0(as.Date(max(t_ee$FarmTimestamp))," ", 4,":00:00"), tz="GMT")
  
}

# Load the model functions ----------------
source(paste0(daughterfolder,"/may_functions.R"), echo=FALSE)

list_f_timestamps <- seq(from=  forecast_timestamp-24*36*3600,
                         to= forecast_timestamp-24*3600,
                         by="6 days")


for (ff in 1:length(list_f_timestamps)){
  
  forecast_timestamp <- list_f_timestamps[ff]
  ## Create the training datasets for the forecast of the three sensors
  
  # select one year
  tobj0<- t_ee[t_ee$FarmTimestamp>=(forecast_timestamp-365*24*3600),]
  tobj0$FarmTime <- tobj0$FarmTimestamp
  tobj0$DateFarm <- as.Date(tobj0$FarmTimestamp)
  
  #tobj0$EnergyCP <- ifelse(is.na(tobj0$EnergyCP),0,tobj0$EnergyCP*2)
  tobj0$EnergyCP <- tobj0$EnergyCP*2
  
  
  


# Forecasting the top bench:
tobj1<- tobj0
tobj1$Sensor_temp <- tobj1$Temperature_FARM_16B1

tobj1 <- tobj1[,c("EnergyCP", "FarmTime", "Sensor_temp", "DateFarm")]

sum(is.na(tobj1$EnergyCP)) #1362

tobj1<-fill_data(tobj1)


# Forecasting the middle bench:
tobj2<- tobj0
tobj2$Sensor_temp <- tobj2$Temperature_Farm_16B2

tobj2 <- tobj2[,c("EnergyCP", "FarmTime", "Sensor_temp", "DateFarm")]

sum(is.na(tobj2$EnergyCP)) #1362

tobj2<-fill_data(tobj2) 


# Forecasting the bottom bench:
tobj3<- tobj0
tobj3$Sensor_temp <- tobj3$Temperature_Farm_16B4

tobj3 <- tobj3[,c("EnergyCP", "FarmTime", "Sensor_temp", "DateFarm")]

sum(is.na(tobj3$EnergyCP)) #1362

tobj3<-fill_data(tobj3)


## Find model fits for three forecasts



## try running bsts ------

liverun_folder <-  paste0(daughterfolder,"/","live_run_save")
setwd(liverun_folder)



sensor_loc <-c("Middle_16B1","Middle_16B2","Middle_16B4")


tobj_list <- list(tobj1,tobj2,tobj3)


# pre-allocate a list of length of nuymber of sensors
list_forecasts <- vector("list", length(tobj_list))
names(list_forecasts) <- sensor_loc
for(mm in 1:length(sensor_loc)){

    sensor_name <-sensor_loc[mm]
    print(sensor_name)
    testtm <- forecast_timestamp
    print(testtm)
    starttm  <-forecast_timestamp- 200*1*24*3600
    
    tobj_mm <- tobj_list[[mm]]

    # runs model and outputs list containing three forecasts, probabilities and warning message
    list_forecasts[[mm]] <- runbsts_live(starttm, testtm, tobj_mm,sensor_name)
 
    
}

setwd(paste0(liverun_folder,"/Data"))
saveRDS(list_forecasts, file=paste0("Forecast_",as.Date(testtm),"_", hour(testtm),"h.RDS"))

# plot the three forecasts: ===========

# plot with previous day
setwd(paste0(liverun_folder,"/Figs"))

# sensor 16 B1
for(mm in 1:length(sensor_loc)){
  
  sensor_name <-sensor_loc[mm]
  print(sensor_name)
  testtm <- forecast_timestamp
  print(testtm)
  
  # select sensor data
  tobj_mm <- tobj_list[[mm]]
  
  # plot two days earlier
    tobj_mm <- tobj_mm[tobj_mm$FarmTime>(forecast_timestamp- 2*1*24*3600),]
  
  f_for <- data.frame(
    FarmTime = seq(from=(forecast_timestamp+1*3600), to= (forecast_timestamp+48*3600), by="1 hour"),
    Dyn_For =  list_forecasts[[mm]][[1]]$mean,
  Stat_lights = list_forecasts[[mm]][[2]]$mean)
  
  f_for <- melt(f_for, id.vars = "FarmTime",value.name = "Sensor_temp",variable.name = "Model") 
  
  tobj_mm$Model <- "observed" 
  
  # data frame to plot:
  tp <- rbind(tobj_mm[, names(f_for)],f_for)

  # extract probility stats for dynamic model
  stats_save <-round(sim_stats_bsts(list_forecasts[[mm]][[1]]),2)
# print warning message based on stats_save
  return_message<- print_warning_message(stats_save)
  
  ggplot(tp, aes(FarmTime, Sensor_temp, colour=Model))+
    geom_point()+geom_line()+
    geom_vline(xintercept = forecast_timestamp)+
    labs(title =paste0("temperature forecast from ",forecast_timestamp," - sensor " , sensor_name), subtitle = return_message)
  ggsave(paste0("Forecast_",sensor_name,"_",as.Date(testtm),".png"))
  
  
}


}
