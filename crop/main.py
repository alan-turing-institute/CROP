import pandas as pd
import create_db
import ingress
import populate_db
import structure
import ReadData
from sqlalchemy import create_engine
from constants import (
    CWD,
    SQL_CONNECTION_STRING_DEFAULT,
    SQL_CONNECTION_STRING_CROP,
    SQL_DBNAME,
    CONST_ADVANTIX_TEST_1
)

from structure import BASE

import sys
print(sys.version)



if __name__ == "__main__":
    
    #import (pd_df, server, db, user, password, port)

    '''Checks if the db and main tables exist in postgres and if not creates them'''
    #create_db.create_database(SQL_DBNAME)

    #Creates an engine which tells sqlalchemy how to talk to a specific db. 
    engine = create_engine(SQL_CONNECTION_STRING_CROP)

    #Creates the tables
    #BASE.metadata.create_all(engine)
    

    '''LOAD DATA IN DB'''
    #read the data
    #ADVANTIX_DF= pd.read_csv(CWD+"\\data\\Advantix\\data-20190821-test1.csv")
    success, log, ADVANTIX_DF=ingress.advantix_import(CWD+"\\data\\Advantix\\"+"data-20190821-test9.csv")
    print (success, log, ADVANTIX_DF)
    #Sensor_Types_data= ReadData.Load_Data("\\data\\Core\\Sensortypes.csv")
    #Sensors = ReadData.Load_Data ("\\data\\Core\\Sensors.csv")
    #Locations = ReadData.Load_Data("\\data\\Core\\locations.csv")

    #populate with csv
    #populate_db.populatesensors(engine, ADVANTIX_DF, structure.Readings_Advantix)
    #populate_db.populatesensors(engine, Sensor_Types_data, structure.Type)
    #populate_db.populatesensors(engine, Sensors, structure.Sensor)
    #populate_db.populatesensors(engine, Locations, structure.Location)
    

    '''Create relationships diagram'''
    #createtables.Creatediagram()
    

    


    
 

 



