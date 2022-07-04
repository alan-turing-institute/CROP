library(DBI)
library(lubridate)

getConnection = function(){
  # TODO These variables need to hold secrets. They should be read from
  # somewhere (envvars?). The below are placeholders.
  crop_host = ""
  crop_port = ""
  crop_dbname = ""
  crop_user = ""
  crop_password = ""
  
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



