library(DBI)
library(lubridate)

getConnection = function(){
  crop_host = "cropapptestsqlserver.postgres.database.azure.com"
  crop_port = "5432"
  crop_dbname = "app_db"
  crop_user = "cropdbadmin@cropapptestsqlserver"
  crop_password = "QhXZ7qZddDr224Mc2P4k"
  
  # Connect to the MySQL database: con
  con <- dbConnect(RPostgreSQL::PostgreSQL(), 
                   dbname = crop_dbname, 
                   host = crop_host, 
                   port = crop_port,
                   user = crop_user,
                   password = crop_password)
  
}

disconnect = function(con) {
  dbDisconnect(con)
}

printTables = function(con) {
  # # Get table names
  tables <- dbListTables(con)
  # Display structure of tables
  str(tables)
}

# Connect to the MySQL database: con
con = getConnection()
printTables(con=con)



