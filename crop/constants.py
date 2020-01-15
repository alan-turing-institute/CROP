import os
import sys

#print (sys.version)

'''Create connection string'''
engine = "postgresql"
dbname = "test"
default_dbname ='postgres'
user_name= "postgres"
password ="crop"
host = "localhost"
port = "5433"

connection_string = "%s://%s:%s@%s:%s/%s" % (engine,user_name,password,host,port,dbname )
connection_string_defaultdb = "%s://%s:%s@%s:%s/%s" % (engine,user_name,password,host,port,default_dbname )
#print (connection_string)

'''Create table list'''
tables= ["sensor", "sensortype", "location",  "readings", "advantix" ]

'''test datasets paths'''
#gets the path of current working directory
cwd = os.getcwd()
sensor_types_path = cwd+"\\Data\\Sensortypes.csv"
Sensors_path = cwd+"\\Data\\Sensors.csv"
locations_path = cwd+"\\Data\\locations.csv"
advantix_data_path =cwd+"\\Data\\Raw\\raw-20191127-pt01.csv"
