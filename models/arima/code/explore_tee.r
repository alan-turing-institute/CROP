
library(zoo)
source(paste0(".","/getData.R"), echo=FALSE)
library(testit)
SENSOR_ID = list(Temperature_FARM_16B1=18, Temperature_Farm_16B2=27, Temperature_Farm_16B4=23)

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

#path_398 = "../data/t_ee_398.RDS"
#tee398 = list(path=path_398, object=readRDS(path_398))

#path_410 = "../data/t_ee_410.RDS"
#tee410 = list(path=path_410, object=readRDS(path_410))

report_Objects = list(tee208)

for (t_object in report_Objects) {
  report_print(t_object)
}

t_object = tee208
startDate = t_object$object$FarmTimestamp[1]
endDate = t_object$object$FarmTimestamp[length(t_object$object$FarmTimestamp)]
numberOfDays = 270
datesToGetData = list(startDate=startDate, endDate=startDate+(numberOfDays * SECONDS.PERDAY))

energy_raw = getEnergyData(limitRows = 0, datesToGetData = datesToGetData)
energy_rds=sprintf("../data/energy_raw.rds")
saveRDS(energy_raw,file = energy_rds)

env_rds=sprintf("../data/env_raw.rds")
env_raw = getTemperatureHumidityData(limitRows = 0, datesToGetData = datesToGetData)
env_raw_sensor18 = env_raw[env_raw[,"sensor_id"]==18,]
saveRDS(env_raw_sensor18, file=env_rds)

testRowCount = function(energy, env, t_ee) {
  assert("Energy has 31296 rows", {
    length(energy$timestamp) == 31296
  })
  assert("Temp/Humidity has 44751 rows", {
    length(env$timestamp) == 44751
  })
}

energy_raw=readRDS(energy_rds)
env_raw=readRDS(env_rds)

#testRowCount(energy_raw, env_raw_sensor18)

testDates = function(energy, env, t_ee) {
  tee_StartDate = as.POSIXct(t_ee$object$FarmTimestamp[1], format="%Y-%m-%d %H:%M:%S", tz="UTC")
  tee_EndDate = as.POSIXct(t_ee$object$FarmTimestamp[length(t_ee$object$FarmTimestamp)], format="%Y-%m-%d %H:%M:%S", tz="UTC")
  tee_Interval = lubridate::interval(startDate, endDate)

  energyAvailabilityStart = as.POSIXct(energy$timestamp[1], format="%Y-%m-%d %H:%M:%S", tz="UTC")
  energyAvailabilityEnd = as.POSIXct(energy$timestamp[length(energy$timestamp)], format="%Y-%m-%d %H:%M:%S", tz="UTC")
  energy_Interval = lubridate::interval(energyAvailabilityStart, energyAvailabilityEnd)

  # Checking start and end date
  assert(sprintf("FarmTimestamp %s",tee_Interval), {
    (t_ee$object$FarmTimestamp[1] == tee_StartDate)
    (t_ee$object$FarmTimestamp[length(t_ee$object$FarmTimestamp)] == tee_EndDate)
  })

  assert(sprintf("Energy %s", energy_Interval), {
    cat (sprintf("Energy interval: %s\n",energy_Interval))
    cat (sprintf("Tee StartDate: %s\n",tee_StartDate))
    cat (sprintf("Tee EndDate: %s\n",tee_EndDate))
    (energyAvailabilityStart %within% tee_Interval)
    (energyAvailabilityEnd %within% tee_Interval)
  })

}

#testEnv = function(env_raw, tee208){
  #assert("env_raw$temperature[1:5] == tee208",{
#  })
#}

#testDates(energy_raw, env_raw, tee208)

source(paste0(".","/may_cleandata.R"), echo=FALSE)
may_208 = readRDS("../data/t_ee_may_208.RDS")
may_208$Temperature_FARM_16B1[12:20]

> tee_208$Temperature_FARM_16B1[1:8]
[1] 20.1750 19.9500 19.6500 19.7000 20.1125 20.6125 22.2500 22.7250
> may_208$Temperature_FARM_16B1[12:20]
[1] 20.4750 19.9500 19.6500 19.7000 20.1125 20.6125 22.2500 22.7250 22.9625
> may_208$Humidity_FARM_16B1[12:20]
[1] 65.50 69.00 73.75 80.50 82.00 76.75 74.00 71.50 69.75
> tee_208$Humidity_FARM_16B1[1:8]
[1] 66.75 69.00 73.75 80.50 82.00 76.75 74.00 71.50
> tee_208$EnergyCP[1:8]
[1] 15.920 15.765 14.585 14.980 16.570 23.665 26.720 26.605
> may_208$EnergyCP[12:20]
[1] 15.920 15.765 14.585 14.980 16.570 23.665 26.720 26.605 27.260
