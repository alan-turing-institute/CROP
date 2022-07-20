"""
Module to define the structure of the database. Each Class, defines a table in the database.
    __tablename__: creates the table with the name given
    __table_args__: table arguments eg: __table_args__ = {'sqlite_autoincrement': True}
    BASE: the declarative_base() callable returns a new base class from which all mapped classes
    should inherit. When the class definition is completed, a new Table and mapper() is generated.
"""
import enum
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Column,
    Enum,
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
    ARANET_TRH_TABLE_NAME,
    ARANET_CO2_TABLE_NAME,
    ARANET_AIRVELOCITY_TABLE_NAME,
    WEATHER_TABLE_NAME,
    WARNINGS_TABLE_NAME,
    MODEL_TABLE_NAME,
    MODEL_MEASURE_TABLE_NAME,
    MODEL_RUN_TABLE_NAME,
    MODEL_PRODUCT_TABLE_NAME,
    MODEL_VALUE_TABLE_NAME,
    TEST_MODEL_TABLE_NAME,
    TEST_MODEL_MEASURE_TABLE_NAME,
    TEST_MODEL_RUN_TABLE_NAME,
    TEST_MODEL_PRODUCT_TABLE_NAME,
    TEST_MODEL_VALUE_TABLE_NAME,
    CROP_TYPE_TABLE_NAME,
    BATCH_TABLE_NAME,
    BATCH_EVENT_TABLE_NAME,
    HARVEST_TABLE_NAME,
)

SQLA = SQLAlchemy()
BASE = SQLA.Model


class ModelClass(BASE):
    """
    This class contains a list of all models running in CROP
    """

    __tablename__ = MODEL_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False, unique=True)
    author = Column(String(100), nullable=False, unique=False)


class ModelMeasureClass(BASE):
    """
    This class contains the names of all columns in models
    """

    __tablename__ = MODEL_MEASURE_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    measure_name = Column(String(100), nullable=False, unique=True)
    measure_description = Column(String(100), nullable=True, unique=False)


class ModelRunClass(BASE):
    """
    This class contains a list of the ids all model runs
    """

    __tablename__ = MODEL_RUN_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    model_id = Column(
        Integer,
        ForeignKey("{}.{}".format(MODEL_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    time_forecast = Column(DateTime())
    time_created = Column(DateTime(), server_default=func.now())

    # arguments
    __table_args__ = (UniqueConstraint("sensor_id", "model_id"),)


class ModelValueClass(BASE):
    """
    This class contains the outputs of model runs
    """

    __tablename__ = MODEL_VALUE_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    product_id = Column(
        Integer,
        ForeignKey("{}.{}".format(MODEL_PRODUCT_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    prediction_value = Column(Float, nullable=False)
    prediction_index = Column(Integer, nullable=False)
    measure_description = Column(String(100), nullable=True, unique=False)

    # arguments
    __table_args__ = (UniqueConstraint("product_id"),)


class ModelProductClass(BASE):
    """
    This class contains the relationships of all model outputs
    """

    __tablename__ = MODEL_PRODUCT_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    run_id = Column(
        Integer,
        ForeignKey("{}.{}".format(MODEL_RUN_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    measure_id = Column(
        Integer,
        ForeignKey("{}.{}".format(MODEL_MEASURE_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    # arguments
    __table_args__ = (UniqueConstraint("run_id", "measure_id"),)


# TODO(mhauru): How to avoid silly duplication of the above classes for the
# test case?
class TestModelClass(BASE):
    """
    This class contains a list of all models running in CROP
    """

    __tablename__ = TEST_MODEL_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False, unique=True)
    author = Column(String(100), nullable=False, unique=False)


class TestModelMeasureClass(BASE):
    """
    This class contains the names of all columns in models
    """

    __tablename__ = TEST_MODEL_MEASURE_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    measure_name = Column(String(100), nullable=False, unique=True)
    measure_description = Column(String(100), nullable=True, unique=False)


class TestModelRunClass(BASE):
    """
    This class contains a list of the ids all model runs
    """

    __tablename__ = TEST_MODEL_RUN_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    model_id = Column(
        Integer,
        ForeignKey("{}.{}".format(TEST_MODEL_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    time_forecast = Column(DateTime())
    time_created = Column(DateTime(), server_default=func.now())

    # arguments
    __table_args__ = (UniqueConstraint("sensor_id", "model_id"),)


class TestModelValueClass(BASE):
    """
    This class contains the outputs of model runs
    """

    __tablename__ = TEST_MODEL_VALUE_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    product_id = Column(
        Integer,
        ForeignKey("{}.{}".format(TEST_MODEL_PRODUCT_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    prediction_value = Column(Float, nullable=False)
    prediction_index = Column(Integer, nullable=False)
    measure_description = Column(String(100), nullable=True, unique=False)

    # arguments
    __table_args__ = (UniqueConstraint("product_id"),)


class TestModelProductClass(BASE):
    """
    This class contains the relationships of all model outputs
    """

    __tablename__ = TEST_MODEL_PRODUCT_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True)
    run_id = Column(
        Integer,
        ForeignKey("{}.{}".format(TEST_MODEL_RUN_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    measure_id = Column(
        Integer,
        ForeignKey("{}.{}".format(TEST_MODEL_MEASURE_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    # arguments
    __table_args__ = (UniqueConstraint("run_id", "measure_id"),)


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

    aranet_code = Column(Unicode(64), nullable=True)
    aranet_pro_id = Column(Unicode(64), nullable=True)
    serial_number = Column(Unicode(128), nullable=True)

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


class ReadingsAranetTRHClass(BASE):
    """
    Base class for the Aranet Temperature and RH GU sensor readings
    """

    __tablename__ = ARANET_TRH_TABLE_NAME

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


class ReadingsAranetCO2Class(BASE):
    """
    Base class for the Aranet CO2  GU sensor readings
    """
    __tablename__ = ARANET_CO2_TABLE_NAME
    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    timestamp = Column(DateTime, nullable=False)
    co2 = Column(Float, nullable=False) # units of parts-per-million

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # arguments
    __table_args__ = (UniqueConstraint("sensor_id", "timestamp"),)


class ReadingsAranetAirVelocityClass(BASE):
    """
    Base class for the Aranet air velocity GU sensor readings.
    Record both the raw current from the sensor, and the corresponding calibrated
    air velocity.
    """
    __tablename__ = ARANET_AIRVELOCITY_TABLE_NAME
    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    timestamp = Column(DateTime, nullable=False)
    current = Column(Float, nullable=True) # raw current, in Amps
    air_velocity = Column(Float, nullable=False) # m/s ?

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # arguments
    __table_args__ = (UniqueConstraint("sensor_id", "timestamp"),)


class ReadingsWeatherClass(BASE):
    """
    Base class for the External weather readings
    """

    __tablename__ = WEATHER_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    timestamp = Column(DateTime, nullable=False)
    temperature = Column(Float, nullable=False)
    rain_probability = Column(Float, nullable=True)
    rain = Column(Float, nullable=True)
    relative_humidity = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    wind_direction = Column(Float, nullable=True)
    air_pressure = Column(Float, nullable=True)
    radiation = Column(Float, nullable=True)
    icon = Column(String(10), nullable=True)
    source = Column(String(50), nullable=True)
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
    # no ref on what that is
    waste_explanation = Column(String, nullable=False)
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


class CropTypeClass(BASE):
    """
    Class for storing types of crop and associated information.
    """

    __tablename__ = CROP_TYPE_TABLE_NAME

    id = Column(Integer, primary_key=True, autoincrement=True)
    growapp_id = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    seed_density = Column(Float, nullable=True)
    propagation_period = Column(Integer, nullable=True)
    grow_period = Column(Integer, nullable=True)
    is_pre_harvest = Column(Boolean, nullable=True)

    # constructor
    def __init__(
        self,
        growapp_id,
        name,
        seed_density,
        propagation_period,
        grow_period,
        is_pre_harvest,
    ):
        self.growapp_id = growapp_id
        self.name = name
        self.seed_density = seed_density
        self.propagation_period = propagation_period
        self.grow_period = grow_period
        self.is_pre_harvest = is_pre_harvest


class BatchClass(BASE):
    """
    Holds static information about each batch being grown in the farm.
    """

    __tablename__ = BATCH_TABLE_NAME

    id = Column(Integer, primary_key=True, autoincrement=True)
    growapp_id = Column(String(100), nullable=False)
    tray_size = Column(Float, nullable=True)
    number_of_trays = Column(Integer, nullable=False)
    crop_type_id = Column(
        Integer,
        ForeignKey("{}.{}".format(CROP_TYPE_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    # constructor
    def __init__(self, growapp_id, tray_size, number_of_trays, crop_type_id):
        self.growapp_id = growapp_id
        self.tray_size = tray_size
        self.number_of_trays = number_of_trays
        self.crop_type_id = crop_type_id


class EventType(enum.Enum):
    none = 0
    weigh = 1
    propagate = 2
    transfer = 3
    harvest = 4
    dry = 5
    edit = 99


class BatchEventClass(BASE):
    """
    New rows are added as a batch moves from one stage to the next
    """

    __tablename__ = BATCH_EVENT_TABLE_NAME

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(
        Integer,
        ForeignKey("{}.{}".format(BATCH_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    # location that is being moved to, if event is moving (null otherwise)
    location_id = Column(
        Integer,
        ForeignKey("{}.{}".format(LOCATION_TABLE_NAME, ID_COL_NAME)),
        nullable=True,
    )
    event_type = Column(Enum(EventType), nullable=False)
    event_time = Column(DateTime, nullable=False)
    next_action_time = Column(DateTime, nullable=True)

    # constructor
    def __init__(self, batch_id, location_id, event_type, event_time, next_action_time):
        self.batch_id = batch_id
        self.location_id = location_id
        self.event_type = event_type
        self.event_time = event_time
        self.next_action_time = next_action_time


class HarvestClass(BASE):
    """
    When a batch is harvested, data will go in here.
    """

    __tablename__ = HARVEST_TABLE_NAME

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_event_id = Column(
        Integer,
        ForeignKey("{}.{}".format(BATCH_EVENT_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    crop_yield = Column(Float, nullable=False)
    waste_disease = Column(Float, nullable=False)
    waste_defect = Column(Float, nullable=False)
    over_production = Column(Float, nullable=False)

    # constructor
    def __init__(
        batch_event_id, crop_yield, waste_disease, waste_defect, over_production
    ):
        self.batch_event_id = batch_event_id
        self.crop_yield = crop_yield
        self.waste_disease = waste_disease
        self.waste_defect = waste_defect
        self.over_production = over_production
