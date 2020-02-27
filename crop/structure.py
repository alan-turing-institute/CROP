"""
Module to define the structure of the database. Each Class, defines a table in the database.
    __tablename__: creates the table with the name given
    __table_args__: table arguments eg: __table_args__ = {'sqlite_autoincrement': True}
    BASE: the declarative_base() callable returns a new base class from which all mapped classes
    should inherit. When the class definition is completed, a new Table and mapper() is generated.
"""

import datetime

from sqlalchemy import (
    ForeignKey,
    Float,
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Unicode,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from crop.constants import (
    SENSOR_TABLE_NAME,
    SENSOR_TYPE_TABLE_NAME,
    LOCATION_TABLE_NAME,
    ADVANTIX_READINGS_TABLE_NAME,
)

BASE = declarative_base()


class Sensor(BASE):
    """
    This class contains a list of all the sensors in the farm
    """

    __tablename__ = SENSOR_TABLE_NAME

    sensor_id = Column(Integer, primary_key=True)
    type_id = Column(
        Integer, ForeignKey(SENSOR_TYPE_TABLE_NAME + ".type_id")
    )  # many to one relationship
    device_id = Column(Unicode(100), nullable=False)
    __table_args__ = (UniqueConstraint("type_id", "device_id", name="_type_device_uc"),)
    # advantix_id = Column(String(100), unique=True, nullable=True) # Modbusid
    # tinytag_id = Column(String(100), unique=True, nullable=True)
    installation_date = Column(DateTime, nullable=False)

    type_relationship = relationship("Type")
    location_relationship = relationship("Location")  # one to many relationship
    advantix_readings_relationship = relationship(
        "Readings_Advantix"
    )  # one to many relationship


class Type(BASE):
    """
    This class contains a list and characteristics of each type of sensor installed eg. "Advantix"
    """

    __tablename__ = SENSOR_TYPE_TABLE_NAME

    type_id = Column(Integer, primary_key=True, unique=True, nullable=False)
    # UUID =   Column(String(36), unique=True, nullable=False)
    sensor_type = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)

    def __repr__(self):
        return "<Type(type_id='%d', sensor_type = %s, description = %s)>" % (
            self.type_id,
            self.sensor_type,
            self.description,
        )


class Location(BASE):
    """
    This class describes all the physical locations in the farm. eg. Sensor x is found in
    the front section, in the left column , in the 3rd self.
    """

    __tablename__ = LOCATION_TABLE_NAME

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer, ForeignKey(SENSOR_TABLE_NAME + ".sensor_id"), nullable=False
    )
    sensor_relationship = relationship(Sensor)
    section = Column(Integer, nullable=False)  # Farm 1/2
    column = Column(Integer, nullable=False)  # no
    shelf = Column(String(50), nullable=False)  # top/middle/bottom
    code = Column(String)


class Readings_Advantix(BASE):
    """
    Base class for the sensor Readings
    """

    __tablename__ = ADVANTIX_READINGS_TABLE_NAME

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer, ForeignKey(SENSOR_TABLE_NAME + ".sensor_id"), nullable=False
    )
    sensor_relationship = relationship(Sensor)
    time_stamp = Column(DateTime, nullable=False)
    temperature = Column(Integer, nullable=False)
    humidity = Column(Integer, nullable=False)
    co2 = Column(Integer, nullable=False)
    time_created = Column(
        DateTime(), server_default=func.now()
    )  # when data are passed to the server
    time_updated = Column(DateTime(), onupdate=func.now())  # <-- to check


class Readings_Tags(BASE):
    """
    Class for reading the raw Advantix data
    """

    __tablename__ = "microtags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(Integer, ForeignKey(SENSOR_TABLE_NAME + ".sensor_id"))
    sensor_relationship = relationship(Sensor)  # back_populates="READINGS"
    loggertimestamp = Column(DateTime)
    deviceaddress = Column(String)
    uptime = Column(Integer)
    battery = Column(Integer)
    validity = Column(Integer)
    ch1 = Column(Integer)
    ch2 = Column(Integer)
    ch3 = Column(Integer)
    opt = Column(Integer)
    co2cozir = Column(Integer)
    tempsht = Column(Integer)
    humiditysht = Column(Integer)
    tempds = Column(Integer)
    time_created = Column(
        DateTime(), server_default=func.now()
    )  # when data are passed to the server
    time_updated = Column(DateTime(), onupdate=func.now())  # <-- to check


class Weather(BASE):
    """
    Class for reading the Met Weather API
    """

    __tablename__ = "weather"

    id = Column(Integer, primary_key=True, autoincrement=True)
    temperature = Column(Integer)
    windspeed = Column(Integer)
    winddirection = Column(Integer)
    weathertype = Column(String)
    forecast = Column(Integer)
    time_accessed = Column(DateTime(), server_default=func.now())
