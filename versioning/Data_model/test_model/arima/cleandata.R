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
  trh_ph <- ddply(trh_sub, .(DatePM,HourPM),
                  summarise,
                  Temperature=mean(temperature, na.rm = T),
                  Humidity=mean(humidity, na.rm = T))
  # create a timestamp corresponding to this hour and date
  trh_ph$Timestamp <- as.POSIXct(paste(trh_ph$DatePM, trh_ph$HourPM),tz="UTC",format="%Y-%m-%d %H")
  
  # Drop lines with NAs, representing the temperature at times between h15-h45 min.
  # apply(trh_ph,2, function(x) sum(is.na(x)))
  trh_ph <- delete.na(trh_ph,1)
  
  # calculate a second hourly average where averaging over the entire hour rather than between xxh45-xxh15.
  trh_ph2 <- ddply(trh_sub, .(Date,Hour),
                   summarise,
                   Temp_hourav=mean(temperature, na.rm = T),
                   Humid_hourav = mean(humidity, na.rm = T))
  trh_ph2$Timestamp <- as.POSIXct(paste(trh_ph2$Date, trh_ph2$Hour),tz="UTC",format="%Y-%m-%d %H")
  trh_ph<- left_join(trh_ph,trh_ph2,by=c("Timestamp") )
  
  trh_ph$FarmTimestamp <- trh_ph$Timestamp
  
  trh_ph_all <- left_join(my_time, trh_ph[c("FarmTimestamp","Timestamp",
                                            "Temperature","Humidity")])
  
  return(trh_ph_all)
}


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
trh$HourPM <- ifelse(abs(trh$Hour+1-trh$HourDec)<=0.25,trh$Hour+1,trh$Hour)
# add special case for midnight!
trh$HourPM <- ifelse(abs(24-trh$HourDec)<=0.25,0,trh$HourPM)

# Create a date column which corresponds to the rounded hour 
trh$Date <- as.Date(trh$Timestamp2)
trh$DatePM <- trh$Date
#trh$DatePM <- as.Date(ifelse(trh$HourPM>=23.5, trh$Date + 1 ,trh$Date), origin = "1970-01-01")
trh$DatePM <- as_date(ifelse(trh$HourPM>=23.5, trh$Date + 1 ,trh$Date), origin = lubridate::origin)

trh$Timestamp <- as.POSIXct(paste(trh$Date, trh$Hour),tz="UTC",format="%Y-%m-%d %H")

# select the time duration over which you want to find new hourly averages 
my_time <- data.frame(FarmTimestamp = seq(from = min(trh$Timestamp)+3600, 
                                          to = max(trh$Timestamp),
                                          by = "1 hour"))

