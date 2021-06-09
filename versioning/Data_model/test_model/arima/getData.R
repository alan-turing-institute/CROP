library(DBI)
library(lubridate)

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


getData = function(numDays, limitRows) {
  
  datesToGetData = getStartEndDate(numDays)
  
  select_command = "SELECT sensors.name, zensie_trh_data.*"
  from_command = "FROM sensor_types, sensors, zensie_trh_data"
  where_criteria1 = "WHERE sensors.id = zensie_trh_data.sensor_id"
  where_criteria2 = sprintf("AND zensie_trh_data.timestamp >= '%s'", datesToGetData$startDate)
  where_criteria3 = sprintf("AND zensie_trh_data.timestamp < '%s'", datesToGetData$endDate)
  
  limit_command = ""
  if (limitRows > 0)
    limit_command = sprintf("LIMIT %i", limitRows)
  sql_command = paste(select_command,from_command, where_criteria1, where_criteria2, where_criteria3, limit_command, sep=" ")
  print (sql_command)
  
  # connect
  conn=connectToDatabase()
  
  data_query = DBI::dbSendQuery(conn=conn, sql_command) 
  data_result = DBI::dbFetch(data_query)
  
  # clean up
  DBI::dbClearResult(data_query)
  disconnectFromDatabase(conn=conn)
  
  data_result
}

getDataFromDatabase = function () {
  env_raw = getData(numDays=30, limitRows=0)
  env_raw$Timestamp2 <- as.POSIXct(env_raw$timestamp,tz="UTC")
  
  env_raw
}

getDataFromCsv = function() {
  env_raw = read.csv("./data/test10.csv")
}

env_raw = getDataFromCsv()

#source(paste0(".","/cleandata.R"), echo=FALSE)

