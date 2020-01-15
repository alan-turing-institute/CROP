#files
import createdb
import createtables
import ReadData 
import populatedb
import mapping
#import test
#libraries
import os
import sys

print (sys.version)

#gets the path of current working directory
CWD = os.getcwd()
#inputs
dbname = 'test4' 
tables= ["sensor", "sensortype", "location",  "readings", "advantix" ]

if __name__ == "__main__":
    
    '''Checks if the db and main tables exist in postgres and if not creates them'''
    createdb.Check_db_Status(dbname, tables)


    '''LOAD DATA IN DB'''
    #read the data
    Advantix_data= ReadData.Readings_Advantix ()
    Sensor_Types_data= ReadData.Readings_SensorTypes()
    Sensors = ReadData.Sensors_List()
    Locations = ReadData.Locations_List()

    #populate with csv
    populatedb.populatesensors(dbname, Sensor_Types_data, createtables.Type)
    populatedb.populatesensors(dbname, Advantix_data, createtables.ReadingsAdvantix)
    populatedb.populatesensors(dbname, Sensors, createtables.Sensor)
    populatedb.populatesensors(dbname, Locations, createtables.Location)
    

    '''Create relationships'''
    #mapping.relationships(dbname)

    


    
 

 



