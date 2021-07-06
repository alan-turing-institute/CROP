library(DBI)
library(lubridate)
require(reshape2)


SECONDS.PERMINUTE = 60
MINS.PERHOUR = 60
HOURS.PERDAY = 24
SECONDS.PERDAY = HOURS.PERDAY * MINS.PERHOUR * SECONDS.PERMINUTE

getStartEndDate = function (numberOfDays) {
  todayDateTime=Sys.time() 
  previousDateTime = Sys.time() - (numberOfDays * SECONDS.PERDAY)
  list(startDate=previousDateTime, endDate=todayDateTime)
}

connectToDatabase = function(){
  crop_host = "cropapptestsqlserver.postgres.database.azure.com"
  crop_port = "5432"
  crop_dbname = "app_db"
  crop_user = "cropdbadmin@cropapptestsqlserver"
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
  
  data_query = DBI::dbSendQuery(conn=conn, sql_command) 
  data_result = DBI::dbFetch(data_query)
  
  # clean up
  DBI::dbClearResult(data_query)
  disconnectFromDatabase(conn=conn)
  
  data_result
}

getTemperatureHumidityData = function(limitRows, datesToGetData) {
  
  select_command = "SELECT sensors.name, zensie_trh_data.*"
  from_command = "FROM sensor_types, sensors, zensie_trh_data"
  where_criteria1 = "WHERE sensors.id = zensie_trh_data.sensor_id"
  where_criteria2 = sprintf("AND zensie_trh_data.timestamp >= '%s'", datesToGetData$startDate)
  where_criteria3 = sprintf("AND zensie_trh_data.timestamp < '%s'", datesToGetData$endDate)
  
  limit_command = ""
  if (limitRows > 0)
    limit_command = sprintf("LIMIT %i", limitRows)
  sql_command = paste(select_command,from_command, where_criteria1, where_criteria2, where_criteria3, limit_command, sep=" ")

  print(sql_command)
  env_raw = getData(sql_command)
  env_raw$Timestamp2 = as.POSIXct(env_raw$timestamp,tz="UTC")
  env_raw
}

getEnergyData = function (limitRows, datesToGetData) {
  
  #"""SELECT * FROM utc_energy_data WHERE utc_energy_data.timestamp >= '%s' AND utc_energy_data.timestamp < '%s'""" % (dt_from, dt_to)
  select_command = "SELECT *"
  from_command = "FROM utc_energy_data"
  where_criteria1 = sprintf("WHERE utc_energy_data.timestamp >= '%s'", datesToGetData$startDate)
  where_criteria2 = sprintf("AND utc_energy_data.timestamp < '%s'", datesToGetData$endDate)
  
  limit_command = ""
  if (limitRows > 0)
    limit_command = sprintf("LIMIT %i", limitRows)
  sql_command = paste(select_command,from_command, where_criteria1, where_criteria2, limit_command, sep=" ")
  
  energy_raw = getData(sql_command)
  energy_raw$Timestamp2 <- as.POSIXct(energy_raw$timestamp,tz="UTC")
  energy_raw
}

getDataFromCsv = function() {
  env_raw = read.csv("./data/test10.csv")
}

numDays = 40
limitRows = 0
datesToGetData = getStartEndDate(numDays)

#energy_raw = getEnergyData(limitRows = limitRows, datesToGetData = datesToGetData)
#write.csv(energy_raw, "./data/energy40.csv")
energy_raw = read.csv("./data/energy40.csv")

#env_raw = getTemperatureHumidityData(limitRows = limitRows, datesToGetData = datesToGetData)
#write.csv(env_raw, "./data/env40.csv")
env_raw = read.csv("./data/env40.csv")

#source(paste0(".","/cleandata.R"), echo=FALSE)

