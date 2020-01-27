import pandas as pd
import create_db
import ingress
from constants import (
    CWD,
    SQL_CONNECTION_STRING_DEFAULT,
    SQL_CONNECTION_STRING_CROP,
    SQL_DBNAME,
    CONST_ADVANTIX_TEST_1
)
#import test
#libraries
import sys

print(sys.version)



if __name__ == "__main__":
    
    

    '''Checks if the db and main tables exist in postgres and if not creates them'''
    #create_db.create_database(SQL_DBNAME)



    '''LOAD DATA IN DB'''
    #read the data
    #ADVANTIX_DF= pd.read_csv(CWD+"\\data\\Advantix\\data-20190821-test1.csv")
    ADVANTIX_DF=ingress.advantix_import(CWD+"\\data\\Advantix\\"+CONST_ADVANTIX_TEST_1)
    print(ADVANTIX_DF[2])
    #Sensor_Types_data= ReadData.Load_Data("\\Data\\Sensortypes.csv")
    #Sensors = ReadData.Load_Data ("\\Data\\Sensors.csv")
    #Locations = ReadData.Load_Data("\\Data\\locations.csv")

    #populate with csv
    #populatedb.populatesensors(dbname, Sensor_Types_data, createtables.Type)
    #populatedb.populatesensors(dbname, Advantix_data, createtables.ReadingsAdvantix)
    #populatedb.populatesensors(dbname, Sensors, createtables.Sensor)
    #populatedb.populatesensors(dbname, Locations, createtables.Location)
    

    '''Create relationships diagram'''
    #createtables.Creatediagram()
    

    


    
 

 



