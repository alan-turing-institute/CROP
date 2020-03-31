import pandas as pd
import numpy as np
import datetime
import psycopg2
from sqlalchemy import (create_engine, ForeignKey, MetaData, Table, Float, Column, Integer, String, DateTime, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, relationship



#NOTE: standard timestamp format from datetime:
#print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.sdatetime.now()))

#Is used to tell SQL that the classes we create are db tables'''
Base = declarative_base()

'''CLASSES WHICH SQLALCHEMY USES TO DEFINE TABLES AND COLUMNS IN THE DB'''
'''Class Sensor contains a list of all the sensors in the farm'''
class Sensor(Base) :
    #Tells SQLAlchemy what the table name is and if there's any table-specific arguments it should know about
    __tablename__= 'sensor'
    #__table_args__ = {'sqlite_autoincrement': True}

    #tell SQLAlchemy the name of column and its attributes:
    id = Column (Integer, primary_key =True) 
    TYPE= Column (String)
    TYPE = Column(Integer, ForeignKey('type.sensortype')) #many to one relationship, inherits the key from the other table. 
    type= relationship("Type")  #defines that is is a relationship
    LOCATION = Column(Integer, ForeignKey('location.id'))
    location = relationship("Location") #many to one relationship

    READINGS = Column(Integer)
    READINGS = relationship ("Readings") #one to many? biodirectional? 
    #INSTALLATIONTIME = Column(DateTime, default=datetime.datetime.utcnow) #picks up current time. 

'''Class SensorType contains a list and characteristics of each type of sensor installed in the farm. eg. "Advantix" '''
class Type(Base):
    __tablename__= 'sensortype'

    id = Column(Integer, primary_key=True)
    UUID =   Column(String(36), unique=True, nullable=False)
    sensortype= Column(String)
    description= Column (String)
   
'''Class Location describes all the physical location in the farm. eg. Sensor A is found in the front section, in the left column , in the 3rd self. ''' 
class Location(Base):
    __tablename__= 'location'

    ID = Column (Integer, primary_key=True)
   #SENSOR_ID= Column(Integer, ForeignKey('Sensor.LOCATION')) # inherits the id from the parent (Sensor class)
    SECTION = Column(Integer) #A/B
    COLUMN = Column (Integer) #no
    SELVE = Column (Integer) #1-4
    CODE = Column (String)



'''Base class for the sensor Readings'''
class Readings(Base):
    __tablename__= 'readings'

    ID = Column (Integer, primary_key=True, autoincrement=True)
    #SENSOR = relationship("Sensor.ID")
    #LOCATIONID = relationship("Sensor.LOCATION")
    TIME_CREATED = Column(DateTime(), server_default=func.now()) #when data are passed to the server
    TIME_UPDATED = Column(DateTime(), onupdate=func.now()) #when data are passed in the sensor <-- to check
    
'''Class for reading the raw Advantix data'''
class ReadingsAdvantix(Base):
    __tablename__= 'advantix'

    id = Column (Integer, primary_key=True, autoincrement=True)
    Battery = Column(Float)
    MODBUSID = Column (Integer)
    TEMPERATURE = Column(Integer)



'''Function to create the database: create_engine('postgresql+psycopg2://user:password@hostname/database_name') '''
def relationships(dbname):
    #connection = engine.connect() #<--dont know what this does... 

    #creates a connection to PostgreSQL
    engine = create_engine('postgresql://postgres:crop@localhost:5433/'+dbname)
    #Creates the database with all the Base Classes
    Base.metadata.create_all(engine)

  