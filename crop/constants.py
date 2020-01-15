"""
A module for constants
"""
import os

# Create connection string
SQL_ENGINE = "postgresql"
SQL_DBNAME = "crop_db"
SQL_DEFAULT_DBNAME ='postgres'
SQL_USER = os.environ['SQL_USER']
SQL_PASSWORD = os.environ['SQL_PASS']
SQL_HOST = "localhost"
SQL_PORT = "5432"

SQL_CONNECTION_STRING = "%s://%s:%s@%s:%s" % (SQL_ENGINE, SQL_USER, SQL_PASSWORD, 
                                                 SQL_HOST, SQL_PORT)

SQL_CONNECTION_STRING_DEFAULT = "%s/%s" % (SQL_CONNECTION_STRING, SQL_DEFAULT_DBNAME)
SQL_CONNECTION_STRING_CROP = "%s/%s" % (SQL_CONNECTION_STRING, SQL_DBNAME)

# connection_string = "%s://%s:%s@%s:%s/%s" % (engine,user_name,password,host,port,dbname )
# connection_string_defaultdb = "%s://%s:%s@%s:%s/%s" % (engine,user_name,password,host,port,default_dbname )
# #print (connection_string)

# '''Create table list'''
# tables= ["sensor", "sensortype", "location",  "readings", "advantix" ]

# '''test datasets paths'''
# #gets the path of current working directory
# cwd = os.getcwd()
# sensor_types_path = cwd+"\\Data\\Sensortypes.csv"
# Sensors_path = cwd+"\\Data\\Sensors.csv"
# locations_path = cwd+"\\Data\\locations.csv"
# advantix_data_path =cwd+"\\Data\\Raw\\raw-20191127-pt01.csv"
