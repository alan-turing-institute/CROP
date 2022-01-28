library(plyr)
library(dplyr)
library(lubridate)
library(reshape2)
library(forecast)

# This script outputs the hourly average temperature, rel hum and energy for the latest data
# It then combines all the data frames using left_join with a time vector called my_time, to be sure the data contains all the timestamps in the last year, even if no data was collected
# 
# load bespoke functions
delete.na <- function(DF, n=0) {
  # By default, it will eliminate all NAs:
  # n is maximum number NAs allowed
  DF[rowSums(is.na(DF)) <= n,]
}

decimal_hour <- function(my_timestamp){
  # my_timestamp must be posixct
  # requires lubridate
  hour(my_timestamp) + minute(my_timestamp) / 60 + second(my_timestamp) / 360
  
}

hourly_av_sensor <- function(trh, sensor_index,my_time){
  
  # subset the data set for the sensor of choice
  trh_sub<- subset(trh, name== sensor_index)
  
  # Find the mean temp and RH for this new HourPM
  trh_ph <- plyr::ddply(trh_sub, .(DatePM,HourPM),
                  summarise,
                  Temperature=mean(temperature, na.rm = T),
                  Humidity=mean(humidity, na.rm = T))
  # create a timestamp corresponding to this hour and date
  trh_ph$Timestamp <- as.POSIXct(paste(trh_ph$DatePM, trh_ph$HourPM),tz="UTC",format="%Y-%m-%d %H")
  
  # Drop lines with NAs, representing the temperature at times between h15-h45 min.
  # apply(trh_ph,2, function(x) sum(is.na(x)))
  trh_ph <- delete.na(trh_ph,1)
  
  # calculate a second hourly average where averaging over the entire hour rather than between xxh45-xxh15.
  trh_ph2 <- plyr::ddply(trh_sub, .(Date,Hour),
                   summarise,
                   Temp_hourav=mean(temperature, na.rm = T),
                   Humid_hourav = mean(humidity, na.rm = T))
  trh_ph2$Timestamp <- as.POSIXct(paste(trh_ph2$Date, trh_ph2$Hour),tz="UTC",format="%Y-%m-%d %H")
  trh_ph<- dplyr::left_join(trh_ph,trh_ph2,by=c("Timestamp") )
  
  trh_ph$FarmTimestamp <- trh_ph$Timestamp
  
  trh_ph_all <- dplyr::left_join(my_time, trh_ph[c("FarmTimestamp","Timestamp",
                                            "Temperature","Humidity")])
  
  return(trh_ph_all)
}

cleanEnvData = function() {
  # Clean env data ===========
  # sort by sensor
  
  # create a copy of env_raw in order to keep the raw file intact and only modify trh
  trh <- (env_raw)
  
  
  # Create two hour columns, one with truncated hour, one with decimal hour
  trh$Hour <- hour(trh$Timestamp2)
  trh$HourDec <- decimal_hour(trh$Timestamp2)
  
  # Create new hour column which encompasses 15 min before and after the hour (PM stands for plus minus)
  trh$HourPM <- ifelse(abs(trh$Hour-trh$HourDec)<=0.25 ,trh$Hour,NA)
  trh$HourPM <- ifelse(abs(trh$Hour+1-trh$HourDec)<=0.25,trh$Hour+1,trh$HourPM)
  # add special case for midnight!
  trh$HourPM <- ifelse(abs(24-trh$HourDec)<=0.25,0,trh$HourPM)
  
  # Create a date column which corresponds to the rounded hour 
  trh$Date <- as.Date(trh$Timestamp2)
  trh$DatePM <- trh$Date
  #trh$DatePM <- as.Date(ifelse(trh$HourPM>=23.5, trh$Date + 1 ,trh$Date), origin = "1970-01-01")
  trh$DatePM <- lubridate::as_date(ifelse(trh$HourPM>=23.5, trh$Date + 1, trh$Date), origin = "1970-01-01")
  
  trh$Timestamp <- as.POSIXct(paste(trh$Date, trh$Hour),tz="UTC",format="%Y-%m-%d %H")
  
  # select the time duration over which you want to find new hourly averages 
  my_time <- data.frame(FarmTimestamp = seq(from = min(trh$Timestamp)+3600, 
                                            to = max(trh$Timestamp),
                                            by = "1 hour"))
  
  # function to find hourly average temperature by sensor
  #
  
  
  # Identify each unique sensor
  sensor_names_from_database <- unique(trh$name)
  sensor_names = c()
  SENSOR_ID = list("FARM_T/RH_16B1"=18, "Farm_T/RH_16B2"=27, "Farm_T/RH_16B4"=23)
  for (n in sensor_names_from_database)
  {
    #print (n)
    if (n %in% names(SENSOR_ID)){
      sensor_names = append(sensor_names, n)
    }
  }
  
  # Select sensors: "FARM_16B1" "FARM_16B4" "Farm_16B2"
  #select_sensors <- sensor_names[c(5,6,7)]
  #sensor_names_2<- gsub("_T/RH", "", select_sensors)
  select_sensors = sensor_names
  sensor_names_2 = gsub("_T/RH", "", select_sensors)
  
  # create list where all sensor data is saved
  all_sensors<- vector(mode = "list", length = length(select_sensors))
  names(all_sensors) <- sensor_names_2
  
  # load hourly average temperature and RH in the list
  for (xx in 1:length(select_sensors)){
    print(sensor_names_2[xx])
    all_sensors[[xx]] <-hourly_av_sensor(trh ,select_sensors[xx],my_time)
  }
  
  # transform the list of data frames into a data frame with ldply
  all_sensors_df <- ldply(all_sensors)
  #all_sensors_df <- dcast(all_sensors_df, FarmTimestamp+Timestamp ~ .id, value.var = c("Temperature","Humidity"))
  #
  # reframe the dataframe so that each column is either temperature or humidity of each sensor
  all_sensors_df <- reshape2::melt(all_sensors_df, measure.vars = c("Temperature","Humidity"))
  
  all_sensors_df2 <- reshape2::dcast(all_sensors_df, FarmTimestamp ~ variable + .id, value.var = c("value"))
  
  saveRDS(all_sensors_df2,"trh_API.RDS")
  
  list(my_time = my_time, all_sensors_df2 = all_sensors_df2)
}

cleanEnergyData = function() {
  ## Clean energy data -----------------------
  ecp <- energy_raw
  
  ecpp <- reshape2::dcast(energy_raw, Timestamp2  ~sensor_id,value.var = "electricity_consumption", mean)
  names(ecpp) <- c("Timestamp2","EnergyCC","EnergyCP")
  
  ecpp$Hour <- hour(ecpp$Timestamp2)
  ecpp$HourDec <- decimal_hour(ecpp$Timestamp2)
  
  # Add column with moving average so that the hourly energy used is the centered average around the hour (because data is half hourly)
  ecpp$ECC_ma <- forecast::ma(ecpp$EnergyCC,order=2)
  ecpp$ECP_ma <- forecast::ma(ecpp$EnergyCP,order=2)
  
  names(ecpp)
  ecpp$Date <- as.Date(ecpp$Timestamp2)
  ecp_ph <- ddply(ecpp, .(Date,Hour),
                  summarise,
                  EnergyCP=mean(EnergyCP, na.rm = T),
                  EnergyCP_ma=first(ECP_ma),
                  EnergyCC=mean(EnergyCC, na.rm = T),
                  EnergyCC_ma=first(ECC_ma))
  ecp_ph$Timestamp <- as.POSIXct(paste(ecp_ph$Date, ecp_ph$Hour),tz="UTC",format="%Y-%m-%d %H")
  
  # Assume ECP is in UTC, but time needs to be shifted back an hour
  ecp_ph$FarmTimestamp <- as.POSIXct(ecp_ph$Timestamp)
  saveRDS(ecp_ph,"ecp_API.RDS")
  ecp_ph
}

## Combine data frames ---------


# check how many rows in data frames to ensure using join function the right direction
# nrow(my_time)
# nrow(my_time) -nrow(all_sensors_df2)
# nrow(my_time) -nrow(ecp_ph)

environmentData = cleanEnvData()
my_time = environmentData$my_time
all_sensors_df2 = environmentData$all_sensors_df2
ecp_ph = cleanEnergyData()

# Join with my_time, which contains every hour in the year (in case of missing data)
t_e1 <- dplyr::left_join(my_time, all_sensors_df2)

# Join with my_time, which contains every hour in the year (in case of missing data)
t_e2 <- dplyr::left_join(my_time, ecp_ph)

# Now can join temperature and energy together
t_ee <- left_join(t_e1, t_e2)

## save the cleaned data frame for future use --------------
#setwd(daughterfolder)

#saveRDS(t_ee,"../data/170D_t_ee.RDS")

