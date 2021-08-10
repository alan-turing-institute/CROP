library(plyr)
require(dplyr)
library(lubridate)
require(reshape2)
require(forecast)
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
  sensor_names <- unique(trh$name)
  
  # Select sensors: "FARM_16B1" "FARM_16B4" "Farm_16B2"
  select_sensors <- sensor_names[c(1,6,9)]
  sensor_names_2<- gsub("_T/RH", "", select_sensors)
  
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
  
  
  

