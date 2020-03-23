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
from sqlalchemy.sql import func

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

from bcrypt import gensalt, hashpw

from crop.constants import (
    SENSOR_TABLE_NAME,
    SENSOR_TYPE_TABLE_NAME,
    LOCATION_TABLE_NAME,
    SENSOR_LOCATION_TABLE_NAME,
    ADVANTIX_READINGS_TABLE_NAME,
    TINYTAGS_READINGS_TABLE_NAME,
    ID_COL_NAME,
)


db = SQLAlchemy()
BASE = db.Model


class TypeClass(BASE):
    """
    This class contains a list and characteristics of each type of sensor installed eg. "Advantix"
    """

    __tablename__ = SENSOR_TYPE_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
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
    id = Column(Integer, primary_key=True, autoincrement=True)
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
    id = Column(Integer, primary_key=True, autoincrement=True)

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

    # constructor
    def __init__(self, section, column, shelf, code):

        self.section = section
        self.column = column
        self.shelf = shelf
        self.code = code


class ReadingsAdvantixClass(BASE):
    """
    Base class for the Advantix sensor readings
    """

    __tablename__ = ADVANTIX_READINGS_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
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
    id = Column(Integer, primary_key=True, autoincrement=True)

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


# class WeatherClass(BASE):
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


class UserClass(BASE, UserMixin):
    """
    Class for storing user credentials.
    """

    __tablename__ = "User"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(LargeBinary, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    def __init__(self, **kwargs):
        for prop, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, "__iter__") and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]
            if prop == "password":
                value = hashpw(value.encode("utf8"), gensalt())
            setattr(self, prop, value)

    def __repr__(self):
        """
        Computes a string reputation of the object.

        """

        return str(self.username)

    def serialize(self):
        """
        Serialization of the object.
        """

        return {"id": self.id, "username": self.username, "email": self.email}
