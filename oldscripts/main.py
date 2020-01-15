#files
import createdb
import createtables
import ReadData 
import populatedb
import constants
#import test
#libraries

import sys

print (sys.version)



if __name__ == "__main__":
    
    '''Checks if the db and main tables exist in postgres and if not creates them'''
    createdb.Check_db_Status(constants.dbname constants.connection_string,constants.connection_string_defaultdb, constants.tables)


    '''LOAD DATA IN DB'''
    #read the data
    Advantix_data= ReadData.Load_Data ("\\Data\\Raw\\raw-20191127-pt01.csv")
    Sensor_Types_data= ReadData.Load_Data("\\Data\\Sensortypes.csv")
    Sensors = ReadData.Load_Data ("\\Data\\Sensors.csv")
    Locations = ReadData.Load_Data("\\Data\\locations.csv")

    #populate with csv
    populatedb.populatesensors(dbname, Sensor_Types_data, createtables.Type)
    populatedb.populatesensors(dbname, Advantix_data, createtables.ReadingsAdvantix)
    populatedb.populatesensors(dbname, Sensors, createtables.Sensor)
    populatedb.populatesensors(dbname, Locations, createtables.Location)
    

    '''Create relationships diagram'''
    createtables.Creatediagram()
    

    


    
 

 



