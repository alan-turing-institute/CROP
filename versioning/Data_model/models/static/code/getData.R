library(DBI)
library(lubridate)
library(reshape2)
library(stringr)

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
  crop_password = "QhXZ7qZddDr224Mc2P4k"
  
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
  
  select_command = "SELECT DISTINCT sensors.name, zensie_trh_data.*"
  from_command = "FROM sensor_types, sensors, zensie_trh_data"
  where_criteria1 = "WHERE sensors.id = zensie_trh_data.sensor_id"
  where_criteria2 = sprintf("AND zensie_trh_data.timestamp >= '%s'", datesToGetData$startDate)
  where_criteria3 = sprintf("AND zensie_trh_data.timestamp < '%s'", datesToGetData$endDate)
  where_criteria4 = sprintf("order by zensie_trh_data.timestamp asc")
  
  limit_command = ""
  if (limitRows > 0)
    limit_command = sprintf("LIMIT %i", limitRows)
  
  sql_command = paste(select_command,from_command, where_criteria1, where_criteria2, where_criteria3, where_criteria4, limit_command, sep=" ")

  print(sql_command)
  env_raw = getData(sql_command)
  env_raw$Timestamp2 = as.POSIXct(env_raw$timestamp,tz="UTC")
  env_raw
}

getEnergyData = function (limitRows, datesToGetData) {
  
  #"""SELECT * FROM utc_energy_data WHERE utc_energy_data.timestamp >= '%s' AND utc_energy_data.timestamp < '%s'""" % (dt_from, dt_to)
  #select_command = "SELECT DATE_TRUNC('', timestamp)"
  #from_command = "FROM utc_energy_data"
  #where_criteria1 = sprintf("WHERE utc_energy_data.timestamp >= '%s'", datesToGetData$startDate)
  #where_criteria2 = sprintf("AND utc_energy_data.timestamp < '%s'", datesToGetData$endDate)
  #where_criteria3 = sprintf("ORDER BY utc_energy_data.timestamp ASC", datesToGetData$endDate)
  
  select_command = "SELECT *" 
  from_command = "FROM utc_energy_data"
  where_criteria1 = sprintf("WHERE utc_energy_data.timestamp BETWEEN '%s'", datesToGetData$startDate)
  where_criteria2 = sprintf("AND '%s'", datesToGetData$endDate)
  where_criteria3 = sprintf("ORDER BY utc_energy_data.timestamp ASC")
  
  limit_command = ""
  if (limitRows > 0){
    limit_command = sprintf("LIMIT %i", limitRows)
  }
  sql_command = paste(select_command,from_command, where_criteria1, where_criteria2, where_criteria3, limit_command, sep=" ")
  
  print(sql_command)
  energy_raw = getData(sql_command)
  energy_raw$Timestamp2 <- as.POSIXct(energy_raw$timestamp,tz="UTC")
  energy_raw
}

daysIntoPast = c(30, 60, 170)
#daysIntoPast = c(1)
limitRows = 0

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

#filename=sprintf("../data/energy%i.rds", numDays)

#write.csv(energy_raw, filename)
#energy_raw = read.csv("../data/energy120.csv")

#env_raw = getTemperatureHumidityData(limitRows = limitRows, datesToGetData = datesToGetData)
#filename=sprintf("../data/env%i.csv", numDays)
#write.csv(env_raw, filename)
#env_raw = read.csv("../data/env120.csv")

#source(paste0(".","/cleandata.R"), echo=FALSE)

