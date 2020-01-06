import sys
import os
import csv
import pandas as pd
import numpy as np
import datetime
import psycopg2
from sqlalchemy import Table, Column, MetaData, Integer, String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

print (sys.version)

CWD = os.getcwd()


#print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.sdatetime.now()))

def Load_Data (filename):
    print ("starting")
    data= np.genfromtxt(file_name, delimiter=',', skipskip_header=1, conconverters= {0: lambda s: str(s)})
    return data

Base = declarative_base()

class Sensor (Base) :
    __tablename__= 'sensor'

    ID= Column (Integer, primary_key =True)
    SENSORTYPEID = Column (Integer)
    LOCATIONID = Column (Integer)
    READINGSID = Column (Integer)
    TIMESTAMP = Column(DateTime, default=datetime.datetime.utcnow)


class SensorType (Base):
    __tablename__= 'sensortype'

    ID = Column(Integer, primary_key=True)
    SENSORTYPE= Column(String(32))
    PARAMETERS= Column (Integer)


class Location (Base):
    #Tell SQLAlchemy what the table name is and if there's any table-specific arguments it should know about
    __tablename__= 'location'
    #__table_args__ = {'sqlite_autoincrement': True}

    #tell SQLAlchemy the name of column and its attributes:
    ID = Column (Integer, primary_key=True)
    SECTION = Column(Integer)
    COLUMN = Column (Integer)
    SELVE = Column (Integer)
    TIMESTAMP = Column(DateTime, default=datetime.datetime.utcnow)


class Readings (Base):
    #Tell SQLAlchemy what the table name is and if there's any table-specific arguments it should know about
    __tablename__= 'readings'

    #tell SQLAlchemy the name of column and its attributes:
    ID = Column (Integer, primary_key=True)
    LOCATIONID = Column (Integer)
    MODBUSID = Column (Integer)
    TIMESTAMP = Column(DateTime, default=datetime.datetime.utcnow)
    TIME_CREATED = Column(DateTime(timezone=True), server_default=func.now())
    TIME_UPDATED = Column(DateTime(timezone=True), onupdate=func.now())
    TEMPERATURE = Column(Integer)


    def __repr__(self):
        return "<Sensor(MODBUSID='{}', TIMESTAMP='{}', TEMPERATURE'{}')>"\
                .format(self.MODBUSID, self.TIMESTAMP, self.TEMPERATURE)

if __name__ == "__main__":
    
    #Create the database: create_engine('postgresql+psycopg2://user:password@hostname/database_name')
    engine = create_engine('postgresql://postgres:crop@localhost:5433/postgres')
    #connection = engine.connect() #<--dont know what this does... 
    Base.metadata.create_all(engine)

    try:
        advantix_cleaned = CWD+ "\\Data\\Cleaned\\data-20190821-pt00.csv"
        advantix_raw = CWD+ "\\Data\\Raw\\raw-20191127-pt01.csv"
        test = "C:\\Users\\Flora\\raw.csv"

        #print (file_name)
        
        data= pd.read_csv(advantix_cleaned)
        datatest= pd.read_csv(advantix_raw)

        #with open(advantix_raw) as csv_file:
        #    csv_reader = csv.reader(csv_file, delimiter=',')
        #    for row in csv_reader:
         #       print(row)


        #data = Load_Data(file_name)
        #print (data)
    except:
        print("An exception occurred")