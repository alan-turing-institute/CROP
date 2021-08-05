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
    Float,
    String,
    DateTime,
    Text,
    Unicode,
    UniqueConstraint,
    LargeBinary,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import false

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

from bcrypt import gensalt, hashpw

from __app__.crop.constants import (
    DAILY_HARVEST_TABLE_NAME,
    SENSOR_TABLE_NAME,
    SENSOR_TYPE_TABLE_NAME,
    LOCATION_TABLE_NAME,
    ADVANTICSYS_READINGS_TABLE_NAME,
    TINYTAG_READINGS_TABLE_NAME,
    AIR_VELOCITY_READINGS_TABLE_NAME,
    ENVIRONMENTAL_READINGS_TABLE_NAME,
    ENERGY_READINGS_TABLE_NAME,
    CROP_GROWTH_TABLE_NAME,
    INFRASTRUCTURE_TABLE_NAME,
    SENSOR_LOCATION_TABLE_NAME,
    ID_COL_NAME,
    SENSOR_UPLOAD_LOG_TABLE_NAME,
    ZENSIE_TRH_TABLE_NAME,
    ZENSIE_WEATHER_TABLE_NAME,
    WARNINGS_TABLE_NAME,
)

SQLA = SQLAlchemy()
BASE = SQLA.Model


class TypeClass(BASE):
    """
    This class contains a list and characteristics of each type of sensor
    installed eg. "Advanticsys"
    """

    __tablename__ = SENSOR_TYPE_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    sensor_type = Column(String(100), nullable=False, unique=True)
    source = Column(String(100), nullable=False)
    origin = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    data = Column(String(100), nullable=False)
    description = Column(Text)

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

    name = Column(Unicode(100), nullable=False)

    last_updated = Column(DateTime())

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # relationshionships (One-To-Many)
    sensor_locations_relationship = relationship("SensorLocationClass")
    advanticsys_readings_relationship = relationship("ReadingsAdvanticsysClass")
    tinytag_readings_relationship = relationship("ReadingsTinyTagClass")
    airvelocity_readings_relationship = relationship("ReadingsAirVelocityClass")
    environmental_readings_relationship = relationship("ReadingsEnvironmentalClass")

    # arguments
    __table_args__ = (UniqueConstraint("type_id", "device_id", name="_type_device_uc"),)


class LocationClass(BASE):
    """
    This class describes all the physical locations in the farm. eg. Sensor x is found in
    the zone Farm 1, in the B aisle, In column 23 in the 4rd self.
        Description of location codes:
        zones: (String) description of zone eg. Entrance, stairs, Farm 1, etc..
        aisle: (String) A, B. (Enumeration of aisles)
        column: (Integer). Enumeration of columns in farm zones.
        shelf: (Integer) Number of shelves per column from bottom to top: 1-4.
    """

    __tablename__ = LOCATION_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)  # e

    zone = Column(String(50), nullable=False)
    aisle = Column(String(50), nullable=False)
    column = Column(Integer, nullable=False)
    shelf = Column(Integer, nullable=False)

    # relationshionships (One-To-Many)
    sensor_locations_relationship = relationship("SensorLocationClass")
    crop_growth_relationship = relationship("CropGrowthClass")

    # arguments
    __table_args__ = (UniqueConstraint("zone", "aisle", "column", "shelf"),)

    # constructor
    def __init__(self, zone, aisle, column, shelf):
        self.zone = zone
        self.aisle = aisle
        self.column = column
        self.shelf = shelf


class ReadingsZensieTRHClass(BASE):
    """
    Base class for the 30MHz Temperature and RH GU sensor readings
    """

    __tablename__ = ZENSIE_TRH_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    timestamp = Column(DateTime, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # arguments
    __table_args__ = (UniqueConstraint("sensor_id", "timestamp"),)


class ReadingsAdvanticsysClass(BASE):
    """
    Base class for the Advanticsys sensor readings
    """

    __tablename__ = ADVANTICSYS_READINGS_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    timestamp = Column(DateTime, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    co2 = Column(Float, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # arguments
    __table_args__ = (UniqueConstraint("sensor_id", "timestamp"),)


class ReadingsAirVelocityClass(BASE):
    """
    Base class for the raw Air Velocity data readings
    """

    __tablename__ = AIR_VELOCITY_READINGS_TABLE_NAME

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    timestamp = Column(DateTime, nullable=False)
    temperature = Column(Float, nullable=False)
    velocity = Column(Float, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())


class ReadingsEnvironmentalClass(BASE):
    """
    Class for reading the custom made Environmental sensor data
    logger_timestamp: ?
    device_timestamp: ?
    uptime: ?
    validity: ?
    ch: channel 0-3 ?
    opt: OPT3001 Ambient Light Sensors (ALS) (lux)
    co2: CO2 using COZIR infrared sensor
    temperature, humidity: Sensirion SHT21 sensor
    tempds: ?

    """

    __tablename__ = ENVIRONMENTAL_READINGS_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    logger_timestamp = Column(DateTime, nullable=False)
    device_timestamp = Column(DateTime, nullable=False)
    device_uid = Column(String, nullable=False)
    uptime = Column(Float, nullable=False)
    battery = Column(Float, nullable=False)
    validity = Column(Float, nullable=False)
    ch0 = Column(Float, nullable=False)
    ch1 = Column(Float, nullable=False)
    ch2 = Column(Float, nullable=False)
    ch3 = Column(Float, nullable=False)
    opt = Column(Float, nullable=False)
    co2 = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    tempds = Column(Float, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())


class ReadingsTinyTagClass(BASE):
    """
    Class for reading the raw tiny tag data
    """

    __tablename__ = TINYTAG_READINGS_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    timestamp = Column(DateTime, nullable=False)
    temperature = Column(Float, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())


class ReadingsEnergyClass(BASE):
    """
    Energy Readings from Stark.co.uk
    """

    __tablename__ = ENERGY_READINGS_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)

    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    timestamp = Column(DateTime, nullable=False)
    electricity_consumption = Column(Float, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # arguments
    __table_args__ = (UniqueConstraint("sensor_id", "timestamp"),)


class DailyHarvestClass(BASE):
    """
    Class for creating the harvest table
    (from manual input)
    """

    __tablename__ = DAILY_HARVEST_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)

    crop = Column(String, nullable=False)
    propagation_date = Column(DateTime, nullable=True)
    location_id = Column(
        Integer,
        ForeignKey("{}.{}".format(LOCATION_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    stack = Column(Integer, nullable=True)
    total_yield_weight = Column(Float, nullable=False)
    disease_trays = Column(Integer, nullable=True)
    defect_trays = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)
    user = Column(String, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())


class CropGrowthClass(BASE):
    """
    Class for reading the crop data
    (from google sheets)
    """

    __tablename__ = CROP_GROWTH_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)

    crop = Column(String, nullable=False)
    propagation_date = Column(DateTime, nullable=False)
    location_id = Column(
        Integer,
        ForeignKey("{}.{}".format(LOCATION_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    trays = Column(Integer, nullable=False)
    m2 = Column(Float, nullable=False)
    supplier = Column(String, nullable=False)
    batch_no = Column(String, nullable=False)
    date_underlight = Column(DateTime, nullable=False)
    week_harvested = Column(DateTime, nullable=False)
    harvest_date = Column(DateTime, nullable=False)
    traceability = Column(String, nullable=False)
    surplus_waste_trays = Column(Float, nullable=False)
    est_disease_trays = Column(Float, nullable=False)
    mass_harvested = Column(Float, nullable=False)
    total_waste_p = Column(Float, nullable=False)  # percentages (?)
    surplus_waste_p = Column(Float, nullable=False)
    total_waste_m2 = Column(String, nullable=False)
    total_waste_p = Column(Float, nullable=False)
    waste_explanation = Column(String, nullable=False)  # no ref on what that is
    yield_m2 = Column(Float, nullable=False)
    propagation_days = Column(Float, nullable=False)
    days_under_lights = Column(Float, nullable=False)
    unique_code = Column(String, nullable=False)
    surplus_wasted = Column(Float, nullable=False)
    x_g = Column(Float, nullable=False)
    total_waste_g = Column(Float, nullable=False)
    projected_yeild_m = Column(Float, nullable=False)
    projected_yield_tot = Column(Float, nullable=False)
    num_trays_wasted = Column(String, nullable=True)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())


class InfrastructureClass(BASE):
    """
    Class for the tank data
    """

    __tablename__ = INFRASTRUCTURE_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)

    tank_time = Column(DateTime, nullable=False)
    tank_no = Column(Integer, nullable=False)
    tank_ph = Column(Float, nullable=False)
    tank_ec = Column(Float)
    tank_clox = Column(Float)
    tank_water_temp = Column(Float)
    # TODO:add entrances


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


class WeatherClass(BASE):
    """
    Class for reading the Met Weather API
    """

    # TODO: connect to met weather api

    __tablename__ = "weather"

    id = Column(Integer, primary_key=True, autoincrement=True)

    temperature = Column(Float, nullable=False)
    rainfall = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    weather_type = Column(String)
    forecast = Column(Float)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())


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


class DataWarningsClass(BASE):
    """
    Class for storing log information for warnings from sensors.
    """

    __tablename__ = WARNINGS_TABLE_NAME

    id = Column(Integer, primary_key=True, autoincrement=True)

    type_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TYPE_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    location_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_LOCATION_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    priority = Column(String(10), nullable=False)
    log = Column(String(100), nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # constructor
    def __init__(self, type_id, location_id, filename, status, log):
        self.type_id = type_id
        self.location_id = location_id
        self.filename = filename
        self.status = status
        self.log = log


class DataUploadLogClass(BASE):
    """
    Class for storing log information from data import procedures.
    """

    __tablename__ = SENSOR_UPLOAD_LOG_TABLE_NAME

    id = Column(Integer, primary_key=True, autoincrement=True)

    type_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TYPE_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    filename = Column(String(100), nullable=False)
    status = Column(String(10), nullable=False)
    log = Column(String(100), nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # constructor
    def __init__(self, type_id, filename, status, log):
        self.type_id = type_id
        self.filename = filename
        self.status = status
        self.log = log
