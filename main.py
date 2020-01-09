import os
import sys
import createdb as db
import ReadData 
import test

print (sys.version)

#gets the path of current working directory
CWD = os.getcwd()

if __name__ == "__main__":
    #read the advantix data
    Advantix_data= ReadData.Readings_Advantix ()
    Sensor_Types_data= ReadData.Readings_SensorTypes()
    #create the database
    db.Createdb(Advantix_data, Sensor_Types_data)
        #Create the database: create_engine('postgresql+psycopg2://user:password@hostname/database_name')
    
    # switch to sqlite. 
    #connection = engine.connect() #<--dont know what this does... 

 



        #with open(advantix_raw) as csv_file:
        #    csv_reader = csv.reader(csv_file, delimiter=',')
        #    for row in csv_reader:
