import sys
import os
import csv
import pandas as pd
import numpy as np
import datetime
import psycopg2
from sqlalchemy import (create_engine, Table, Float, Column, MetaData, Integer, String, DateTime, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker

print (sys.version)

CWD = os.getcwd()
#sqlite

#print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.sdatetime.now()))

def Load_Data (filename):
    print ("starting")
    data= np.genfromtxt(file_name, delimiter=',', skipskip_header=1, conconverters= {0: lambda s: str(s)})
    return data

'''Create classes for sensors'''
Base = declarative_base()

class Sensor (Base) :
    #says the name of the new table in postgresql
    __tablename__= 'sensor'

    #Column names
    ID = Column (Integer, primary_key =True)
    SENSORTYPEID = Column (Integer)
    LOCATIONID = Column (Integer)
    READINGSID = Column (Integer)
    INSTALLATIONTIME = Column(DateTime, default=datetime.datetime.utcnow) #


class SensorType (Base):
    __tablename__= 'sensortype'

    ID = Column(Integer, primary_key=True)
    SENSORTYPE= Column(String(32))
    DESCRIPTION= Column (Text) 
   

class Location (Base):
    #Tell SQLAlchemy what the table name is and if there's any table-specific arguments it should know about
    __tablename__= 'location'
    #__table_args__ = {'sqlite_autoincrement': True}

    #tell SQLAlchemy the name of column and its attributes:
    ID = Column (Integer, primary_key=True)
    SECTION = Column(Integer) #F/M/B
    COLUMN = Column (Integer) #L/R
    SELVE = Column (Integer) #U/M/D
    


class Readings (Base):
    #Tell SQLAlchemy what the table name is and if there's any table-specific arguments it should know about
    __tablename__= 'Sensorclass'

    #tell SQLAlchemy the name of column and its attributes:
    ID = Column (Integer, primary_key=True, autoincrement=True)
    LOCATIONID = Column (Integer)
    TIME_CREATED = Column(DateTime(), server_default=func.now()) #when data are passed to the server
    TIME_UPDATED = Column(DateTime(), onupdate=func.now()) #when data are passed in the sensor <-- to check
    

class ReadingsAdvantix (Readings):
  
    Battery = Column(Float)
    MODBUSID = Column (Integer)
    TEMPERATURE = Column(Integer)

def Readings_Advantix ():
    try:
        #how to i turn this to a test?
        #advantix_cleaned = CWD+ "\\Data\\Cleaned\\data-20190821-pt00.csv"
        advantix_raw_path = CWD + "\\Data\\Raw\\raw-20191127-pt01.csv"
        #data= pd.read_csv(advantix_cleaned)
        advantix_raw= pd.read_csv(advantix_raw_path)
        print (advantix_raw.head())

    except:
        print("Can't read advantix data")
    return (advantix_raw)


if __name__ == "__main__":
    Advantix_Raw= Readings_Advantix ()

    #Create the database: create_engine('postgresql+psycopg2://user:password@hostname/database_name')
    
    # switch to sqlite. 
    #connection = engine.connect() #<--dont know what this does... 

    try: 
        engine = create_engine('postgresql://postgres:crop@localhost:5433/postgres')
        Base.metadata.create_all(engine)
        session = sessionmaker()
        session.configure(bind=engine)
        
        s = session()
        #s.add(Rawdata)
        
        s.bulk_insert_mappings(ReadingsAdvantix, Advantix_Raw.to_dict(orient="records"))
        s.commit()
      
        
    except:
        print ("didnt work")
    finally:
        s.close()


        #with open(advantix_raw) as csv_file:
        #    csv_reader = csv.reader(csv_file, delimiter=',')
        #    for row in csv_reader:
        #       print(row)


        #data = Load_Data(file_name)
        #print (data)
    