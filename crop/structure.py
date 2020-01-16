"""
Module to define the structure of the database. Each Class, defines a table in the database.
    __tablename__: creates the table with the name given
    __table_args__: table arguments eg: __table_args__ = {'sqlite_autoincrement': True}
    BASE: the declarative_base() callable returns a new base class from which all mapped classes
    should inherit. When the class definition is completed, a new Table and mapper() is generated.
"""

import datetime

from sqlalchemy import (ForeignKey, Float, Column, Integer, String, DateTime, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from constants import (
    SENSOR_TABLE_NAME,
    SENSOR_TYPE_TABLE_NAME,
    LOCATION_TABLE_NAME,
    ADVANTIX_READINGS_TABLE_NAME
    )


BASE = declarative_base()

class Sensor(BASE):
    """
    This class contains a list of all the sensors in the farm
    """

    __tablename__ = SENSOR_TABLE_NAME

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey(SENSOR_TYPE_TABLE_NAME+'.id')) #many to one relationship
    type_relationship = relationship("Type")
    location_relationship = relationship("Location") #one to many relationship
    advantix_readings_relationship = relationship("Readings") #one to many relationship
    installation_time = Column(DateTime, default=datetime.datetime.utcnow) #picks up current time.


class Type(BASE):
    """
    This class contains a list and characteristics of each type of sensor installed eg. "Advantix"
    """
    __tablename__ = SENSOR_TYPE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    #UUID =   Column(String(36), unique=True, nullable=False)
    sensor_type = Column(String)
    description = Column(Text)


class Location(BASE):
    """
    This class describes all the physical locations in the farm. eg. Sensor x is found in
    the front section, in the left column , in the 3rd self.
    """

    __tablename__ = LOCATION_TABLE_NAME

    id = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, ForeignKey(SENSOR_TABLE_NAME+'.id'))
    sensor_relationship = relationship(Sensor, back_populates="sensors")
    section = Column(Integer) #A/B
    column = Column(Integer) #no
    shelf = Column(Integer) #1-4
    code = Column(String)


class Readings(BASE):
    """
    Base class for the sensor Readings
    """

    __tablename__ = ADVANTIX_READINGS_TABLE_NAME

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(Integer, ForeignKey(SENSOR_TABLE_NAME+'.id'))
    sensor_relationship = relationship(Sensor, back_populates="READINGS")
    battery = Column(Float)
    modbusid = Column(Integer)
    temperature = Column(Integer)
    time_created = Column(DateTime(), server_default=func.now()) #when data are passed to the server
    time_updated = Column(DateTime(), onupdate=func.now()) #<-- to check


class Readings_Advantix(BASE):
    """
    Class for reading the raw Advantix data
    """
    __tablename__ = "temp"

    id = Column(Integer, primary_key=True, autoincrement=True)
    battery = Column(Float)
    modbusid = Column(Integer)
    temperature = Column(Integer)
