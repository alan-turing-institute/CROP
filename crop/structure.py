"""
Module to define the structure of the database. Each Class, defines a table in the database.
    __tablename__: creates the table with the name given
    __table_args__: table arguments eg: __table_args__ = {'sqlite_autoincrement': True}
    BASE: the declarative_base() callable returns a new base class from which all mapped classes
    should inherit. When the class definition is completed, a new Table and mapper() is generated.
"""

from sqlalchemy import (
    ForeignKey,
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Unicode,
    UniqueConstraint,
    LargeBinary,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from crop.constants import (
    SENSOR_TABLE_NAME,
    SENSOR_TYPE_TABLE_NAME,
    LOCATION_TABLE_NAME,
    SENSOR_LOCATION_TABLE_NAME,
    ADVANTIX_READINGS_TABLE_NAME,
    TINYTAGS_READINGS_TABLE_NAME,
    ID_COL_NAME,
)

BASE = declarative_base()


class TypeClass(BASE):
    """
    This class contains a list and characteristics of each type of sensor installed eg. "Advantix"
    """

    __tablename__ = SENSOR_TYPE_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    sensor_type = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # relationshionships (One-To-Many)
    sensors_relationship = relationship("SensorClass")


class SensorClass(BASE):
    """
    This class contains a list of all the sensors in the farm
    """

    __tablename__ = SENSOR_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    type_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TYPE_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    device_id = Column(Unicode(100), nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # relationshionships (One-To-Many)
    sensor_locations_relationship = relationship("SensorLocationClass")

    advantix_readings_relationship = relationship("ReadingsAdvantixClass")
    tinytags_readings_relationship = relationship("ReadingsTinyTagsClass")

    # arguments
    __table_args__ = (UniqueConstraint("type_id", "device_id", name="_type_device_uc"),)


class LocationClass(BASE):
    """
    This class describes all the physical locations in the farm. eg. Sensor x is found in
    the front section, in the left column , in the 3rd self.
    """

    __tablename__ = LOCATION_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)

    section = Column(Integer, nullable=False)  # Farm 1/2
    column = Column(Integer, nullable=False)  # no
    shelf = Column(String(50), nullable=False)  # top/middle/bottom

    code = Column(String, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # relationshionships (One-To-Many)
    sensor_locations_relationship = relationship("SensorLocationClass")

    # arguments
    __table_args__ = (UniqueConstraint("section", "column", "shelf"),)


class ReadingsAdvantixClass(BASE):
    """
    Base class for the Advantix sensor readings
    """

    __tablename__ = ADVANTIX_READINGS_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    time_stamp = Column(DateTime, nullable=False)
    temperature = Column(Integer, nullable=False)
    humidity = Column(Integer, nullable=False)
    co2 = Column(Integer, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())


class ReadingsTinyTagsClass(BASE):
    """
    Class for reading the raw Advantix data
    """

    __tablename__ = TINYTAGS_READINGS_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    loggertimestamp = Column(DateTime, nullable=False)
    deviceaddress = Column(String, nullable=False)
    uptime = Column(Integer, nullable=False)
    battery = Column(Integer, nullable=False)
    validity = Column(Integer, nullable=False)
    ch1 = Column(Integer, nullable=False)
    ch2 = Column(Integer, nullable=False)
    ch3 = Column(Integer, nullable=False)
    opt = Column(Integer, nullable=False)
    co2cozir = Column(Integer, nullable=False)
    tempsht = Column(Integer, nullable=False)
    humiditysht = Column(Integer, nullable=False)
    tempds = Column(Integer, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())


class SensorLocationClass(BASE):
    """
    Class for storing sensor location history.
    """

    __tablename__ = SENSOR_LOCATION_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)

    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    location_id = Column(
        Integer,
        ForeignKey("{}.{}".format(LOCATION_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    installation_date = Column(DateTime, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # arguments
    __table_args__ = (UniqueConstraint("sensor_id", "installation_date"),)


class UserClass(BASE):
    """
    Class for user data
    """

    __tablename__ = "User"

    id = Column(Integer, primary_key=True)

    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(LargeBinary, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

# class Weather(BASE):
#     """
#     Class for reading the Met Weather API
#     """

#     __tablename__ = "weather"

#     id = Column(Integer, primary_key=True, autoincrement=True)

#     temperature = Column(Integer)
#     windspeed = Column(Integer)
#     winddirection = Column(Integer)
#     weathertype = Column(String)
#     forecast = Column(Integer)
#     time_accessed = Column(DateTime(), server_default=func.now())
