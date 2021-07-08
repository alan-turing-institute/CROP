library(DBI)
library(lubridate)
require(reshape2)

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
  print (sprintf("Running SQL: %s",sql_command))
  conn=connectToDatabase()
  
  data_query = DBI::dbSendQuery(conn=conn, sql_command) 
  data_result = DBI::dbFetch(data_query)
  
  # clean up
  DBI::dbClearResult(data_query)
  disconnectFromDatabase(conn=conn)
  
  print(data_result)
}

writeData = function(sql_command) {
  # connect
  print (sprintf("Running SQL: %s",sql_command))
  conn=connectToDatabase()
  
  data_query = DBI::dbSendQuery(conn=conn, sql_command) 
  data_result = DBI::dbFetch(data_query)
  
  # clean up
  DBI::dbClearResult(data_query)
  disconnectFromDatabase(conn=conn)
  
  data_result
}

getPredictions = function(limitRows) {
  select_command = "SELECT *"
  from_command = "FROM model_prediction"
  limit_command = ""
  if (limitRows > 0)
    limit_command = sprintf("LIMIT %i", limitRows)
  sql_command = paste(select_command,from_command, limit_command, sep=" ")
  getData(sql_command)
}

writeRun=function(model_id, sensor_id, measure_id) {
  #INSERT INTO model_run(sensor_id, measure_id, model_id)
  table_name = "model_run"
  insert_command = sprintf("Insert into %s (sensor_id, measure_id, model_id) values", table_name)
  value_command = sprintf("(%i,%i,%i)", sensor_id, measure_id, model_id)
  return_command = "RETURNING id"
  sql_command = paste(insert_command,value_command, return_command, sep=" ")
  run = writeData(sql_command = sql_command)
  run
}

writePrediction = function(run_id, values){
  #(run_id,prediction_value, prediction_index)
  if (length(values)>0){
    table_name = "model_prediction"
    insert_command = sprintf("Insert into %s (run_id, prediction_index, prediction_value) values", table_name)
    print(run_id)
    value_command = sprintf("(%i,%i,%f)", run_id, 1, values[1])
    for (v in 2:length(values)) {
      value_command = paste(value_command, sprintf("(%i,%i,%f)", run_id, v, values[v]), sep=",")
    }
    return_command = "RETURNING *"
    sql_command = paste(insert_command, value_command, return_command, sep=" ")
    writeData(sql_command = sql_command)
  }
}

