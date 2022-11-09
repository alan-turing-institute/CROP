library(DBI)
library(lubridate)
library(reshape2)
library(stringr)

SECONDS.PERMINUTE = 60
MINS.PERHOUR = 60
HOURS.PERDAY = 24
SECONDS.PERDAY = HOURS.PERDAY * MINS.PERHOUR * SECONDS.PERMINUTE

getStartEndDate = function (numberOfDays) {
  # Returns a list with elements "startDate" and "endDate".
  # "startDate" is the datetime "numberOfDays" ago.
  # "endDate" is the current datetime.
  todayDateTime=Sys.time()
  previousDateTime = Sys.time() - (numberOfDays * SECONDS.PERDAY)
  list(startDate=previousDateTime, endDate=todayDateTime)
}

getStartDate = function (numberOfDays, forecastDate) {
  # Returns a list with elements "startDate" and "endDate".
  # "startDate" is the datetime "numberOfDays" before "forecastDate".
  # "endDate" is just "forecastDate".
  date_dataStarts = forecastDate-(numberOfDays*SECONDS.PERDAY)
  list(startDate=date_dataStarts, endDate=forecastDate)
}

connectToDatabase = function(){
  # Connect to DataBase using RPostgreSQL (uses DBI)
  # TODO These variables need to hold secrets. They should be read from
  # somewhere (envvars?). The below are placeholders.
  crop_host = ""
  crop_port = ""
  crop_dbname = ""
  crop_user = ""
  crop_password = ""

  # Connect to the MySQL database: con
  con <- DBI::dbConnect(RPostgreSQL::PostgreSQL(),
                   dbname = crop_dbname,
                   host = crop_host,
                   port = crop_port,
                   user = crop_user,
                   password = crop_password)

}

disconnectFromDatabase = function(conn) {
  DBI::dbDisconnect(conn)
}

printTables = function(conn) {
  # # Get table names
  tables <- dbListTables(conn)
  # Display structure of tables
  str(tables)
}

getData = function(sql_command) {
  # connect
  conn=connectToDatabase()

  data_query = DBI::dbSendQuery(conn=conn, sql_command) # submits and synchronously executes the SQL query to the database engine
  data_result = DBI::dbFetch(data_query) # extracts records from database using the query above

  # clean up
  DBI::dbClearResult(data_query) # this needs to be run after fetching the requested records
  disconnectFromDatabase(conn=conn)

  data_result
}

getTemperatureHumidityData = function(limitRows, datesToGetData) {
  # fetches weather data from the database over the requested time period using the specifications below
  select_command = "SELECT DISTINCT sensors.name, aranet_trh_data.*"
  from_command = "FROM sensor_types, sensors, aranet_trh_data"
  where_criteria1 = "WHERE sensors.id = aranet_trh_data.sensor_id"
  where_criteria2 = sprintf("AND aranet_trh_data.timestamp >= '%s'", datesToGetData$startDate)
  where_criteria3 = sprintf("AND aranet_trh_data.timestamp < '%s'", datesToGetData$endDate)
  where_criteria4 = sprintf("order by aranet_trh_data.timestamp asc")

  limit_command = ""
  if (limitRows > 0)
    limit_command = sprintf("LIMIT %i", limitRows)

  # paste: takes multiple elements from the multiple vectors and concatenates them into a single element
  sql_command = paste(select_command,from_command, where_criteria1, where_criteria2, where_criteria3, where_criteria4, limit_command, sep=" ")

  print(sql_command)
  env_raw = getData(sql_command)
  env_raw$Timestamp2 = as.POSIXct(env_raw$timestamp,tz="UTC") # create new colunm "Timestamp2" in "env_raw" dataframe - specify UTC time-zone in the conversion
  env_raw
}

getEnergyData = function (limitRows, datesToGetData) {
  # fetches energy data from the database over the requested time period using the specifications below

  #"""SELECT * FROM utc_energy_data WHERE utc_energy_data.timestamp >= '%s' AND utc_energy_data.timestamp < '%s'""" % (dt_from, dt_to)
  select_command = "SELECT *"
  from_command = "FROM utc_energy_data"
  where_criteria1 = sprintf("WHERE utc_energy_data.timestamp >= '%s'", datesToGetData$startDate)
  where_criteria2 = sprintf("AND utc_energy_data.timestamp < '%s'", datesToGetData$endDate)
  where_criteria3 = sprintf("ORDER BY utc_energy_data.timestamp ASC")

  #select_command = "SELECT *"
  #from_command = "FROM utc_energy_data"
  #where_criteria1 = sprintf("WHERE cast(utc_energy_data.timestamp as timestamp)  BETWEEN '%s'", datesToGetData$startDate)
  #where_criteria2 = sprintf("AND '%s'", datesToGetData$endDate)
  #where_criteria3 = sprintf("ORDER BY utc_energy_data.timestamp ASC")

  limit_command = ""
  if (limitRows > 0){
    limit_command = sprintf("LIMIT %i", limitRows)
  }
  sql_command = paste(select_command,from_command, where_criteria1, where_criteria2, where_criteria3, limit_command, sep=" ")

  print(sql_command)
  energy_raw = getData(sql_command)
  energy_raw$Timestamp2 = as.POSIXct(energy_raw$timestamp,tz="UTC")
  #energy_raw$timestamp = with_tz(energy_raw$timestamp,tz="UTC")
  energy_raw
}

createHistoryData = function() {
  daysIntoPast = c(30, 60, 170) #c: combine values into a vector or list
  #daysIntoPast = c(1)
  limitRows = 0

  # loop through daysIntoPast and fetch energy and weather data for that time period
  # write the fetched data to csv and rds files
  for (numDays in 1: length(daysIntoPast)) {
    limitRows = 0
    datesToGetData = getStartEndDate(daysIntoPast[numDays])

    energy_raw = getEnergyData(limitRows = limitRows, datesToGetData = datesToGetData)
    energy_csv=sprintf("../data/energy%i.csv", daysIntoPast[numDays])
    print(energy_csv)
    energy_rds=sprintf("../data/energy%i.rds", daysIntoPast[numDays])
    write.csv(energy_raw, energy_csv)
    saveRDS(energy_raw,energy_rds)

    env_raw = getTemperatureHumidityData(limitRows = limitRows, datesToGetData = datesToGetData)
    env_csv=sprintf("../data/env%i.csv", daysIntoPast[numDays])
    print(env_csv)
    env_rds=sprintf("../data/env%i.rds", daysIntoPast[numDays])
    write.csv(env_raw, env_csv)
    saveRDS(env_raw,env_rds)
  }
}

createLatestData = function(numDays) {
  # fetch weather and energy data since "numDays" ago
  limitRows = 0
  datesToGetData = getStartEndDate(numDays)
  energy_raw = getEnergyData(limitRows = limitRows, datesToGetData = datesToGetData)
  env_raw = getTemperatureHumidityData(limitRows = limitRows, datesToGetData = datesToGetData)
  list(dates = datesToGetData, energy = energy_raw, env=env_raw)
}

createGivenDateData = function(date_Forecast, numDays) {
  # fetch weather and energy data over specified time period
  limitRows = 0
  datesToGetData = getStartDate(numberOfDays = numDays, forecastDate = date_Forecast)
  energy_raw = getEnergyData(limitRows = limitRows, datesToGetData = datesToGetData)
  env_raw = getTemperatureHumidityData(limitRows = limitRows, datesToGetData = datesToGetData)
  list(dates = datesToGetData, energy = energy_raw, env=env_raw)
}

if (exists("date_Forecast")==FALSE)
  date_Forecast = as.POSIXct('2021-11-08 12:00:00', format="%Y-%m-%d %H:%M:%S", tz="UTC") #TODO why is this the default date?
if (exists("numDaysTraining")==FALSE)
  numDaysTraining = 200

configData = createGivenDateData(date_Forecast=date_Forecast, numDays = numDaysTraining)
env_raw = configData$env
energy_raw = configData$energy
