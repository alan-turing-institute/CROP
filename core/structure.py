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
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
    Unicode,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import false

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

from bcrypt import gensalt, hashpw

from .constants import (
    SENSOR_TABLE_NAME,
    SENSOR_TYPE_TABLE_NAME,
    LOCATION_TABLE_NAME,
    ADVANTICSYS_READINGS_TABLE_NAME,
    TINYTAG_READINGS_TABLE_NAME,
    ENERGY_READINGS_TABLE_NAME,
    SENSOR_LOCATION_TABLE_NAME,
    ID_COL_NAME,
    SENSOR_UPLOAD_LOG_TABLE_NAME,
    ARANET_TRH_TABLE_NAME,
    ARANET_CO2_TABLE_NAME,
    ARANET_AIRVELOCITY_TABLE_NAME,
    AEGIS_IRRIGATION_TABLE_NAME,
    WEATHER_TABLE_NAME,
    WEATHER_FORECAST_TABLE_NAME,
    MODEL_TABLE_NAME,
    MODEL_MEASURE_TABLE_NAME,
    MODEL_RUN_TABLE_NAME,
    MODEL_PRODUCT_TABLE_NAME,
    MODEL_VALUE_TABLE_NAME,
    CROP_TYPE_TABLE_NAME,
    BATCH_TABLE_NAME,
    BATCH_EVENT_TABLE_NAME,
    HARVEST_TABLE_NAME,
    WARNING_TYPES_TABLE_NAME,
    WARNINGS_TABLE_NAME,
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
    aisle = Column(String(50), nullable=True)
    column = Column(Integer, nullable=True)
    shelf = Column(Integer, nullable=True)

    # relationshionships (One-To-Many)
    sensor_locations_relationship = relationship("SensorLocationClass")

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

    timestamp = Column(DateTime, nullable=False, index=True)
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

    timestamp = Column(DateTime, nullable=False, index=True)
    co2 = Column(Float, nullable=False)  # units of parts-per-million

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

    timestamp = Column(DateTime, nullable=False, index=True)
    current = Column(Float, nullable=True)  # raw current, in Amps
    air_velocity = Column(Float, nullable=False)  # m/s ?

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # arguments
    __table_args__ = (UniqueConstraint("sensor_id", "timestamp"),)


class ReadingsAegisIrrigationClass(BASE):
    """
    Base class for the Aegis II irrigation readings.
    Record temperature, pH, dissolved oxygen, conductivity,
    and turbidity, of the water in the farm.
    """

    __tablename__ = AEGIS_IRRIGATION_TABLE_NAME
    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )

    timestamp = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float, nullable=True)  # in degrees Celsius
    pH = Column(Float, nullable=False)
    dissolved_oxygen = Column(Float, nullable=False)
    conductivity = Column(Float, nullable=False)
    turbidity = Column(Float, nullable=False)
    peroxide = Column(Float, nullable=False)

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

    timestamp = Column(DateTime, nullable=False, index=True)
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

    timestamp = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    co2 = Column(Float, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # arguments
    __table_args__ = (UniqueConstraint("sensor_id", "timestamp"),)


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

    timestamp = Column(DateTime, nullable=False, index=True)
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

    timestamp = Column(DateTime, nullable=False, index=True)
    electricity_consumption = Column(Float, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    # arguments
    __table_args__ = (UniqueConstraint("sensor_id", "timestamp"),)


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
    growapp_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
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
    growapp_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
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
    growapp_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    event_type = Column(Enum(EventType), nullable=False)
    event_time = Column(DateTime, nullable=False, index=True)
    next_action_time = Column(DateTime, nullable=True)

    # constructor
    def __init__(
        self,
        growapp_id,
        batch_id,
        location_id,
        event_type,
        event_time,
        next_action_time,
    ):
        self.growapp_id = growapp_id
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
    # note that the growapp_id is a key to the Grow Batch table
    growapp_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    location_id = Column(
        Integer,
        ForeignKey("{}.{}".format(LOCATION_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    crop_yield = Column(Float, nullable=False)
    waste_disease = Column(Float, nullable=False)
    waste_defect = Column(Float, nullable=False)
    over_production = Column(Float, nullable=False)

    # constructor
    def __init__(
        self,
        batch_event_id,
        growapp_id,
        location_id,
        crop_yield,
        waste_disease,
        waste_defect,
        over_production,
    ):
        self.batch_event_id = batch_event_id
        self.growapp_id = growapp_id
        self.location_id = location_id
        self.crop_yield = crop_yield
        self.waste_disease = waste_disease
        self.waste_defect = waste_defect
        self.over_production = over_production


class WarningTypeClass(BASE):
    """
    Table for different types of warnings CROP may report.

    The short_description and long_description columns should be either strings that are
    shown in any logging/reporting interface for warnings of this type, or templates for
    such strings. A template can hold various placeholders that are to be filled in with
    extra data for each particular error. How these placeholders are specified and how
    they are to be filled in is not specified by the database schema, but is the
    responsibility of the logging/reporting code.

    Category is a string that groups the rows of this table into broader classes, such
    as "Farm condition warnings" or "Forecasting model warnings". The front end displays
    warnings grouped by these categories.
    """

    __tablename__ = WARNING_TYPES_TABLE_NAME
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True)
    short_description = Column(Unicode(256), nullable=False)
    long_description = Column(Unicode(2048), nullable=True)
    time_created = Column(DateTime(), nullable=True, server_default=func.now())
    category = Column(Unicode(256), nullable=True)


class WarningClass(BASE):
    """
    Table for warnings CROP reports.

    time_created is for when this warning was created, time is for any other time
    variable that may be relevant for the warning.

    The sensor_id, batch_id, and time columns are nullable because many warning types
    may have no use for them. Any extra data other than an attached sensor, batch, or
    timestamp should be recorded in the other_data column. How the data in that column
    is to be interpreted depends on the warning type, and is something the code
    processing the warnings needs to take care of.

    Priority should be a positive integer, with higher values meaning higher priority.
    """

    __tablename__ = WARNINGS_TABLE_NAME

    id = Column(Integer, primary_key=True, autoincrement=True)
    warning_type_id = Column(
        Integer,
        ForeignKey("{}.{}".format(WARNING_TYPES_TABLE_NAME, ID_COL_NAME)),
        nullable=False,
    )
    sensor_id = Column(
        Integer,
        ForeignKey("{}.{}".format(SENSOR_TABLE_NAME, ID_COL_NAME)),
        nullable=True,
    )
    batch_id = Column(
        Integer,
        ForeignKey("{}.{}".format(BATCH_TABLE_NAME, ID_COL_NAME)),
        nullable=True,
    )
    time = Column(DateTime(), nullable=True, server_default=func.now())
    other_data = Column(JSON, nullable=True)
    priority = Column(Integer, nullable=True)
    time_created = Column(DateTime(), nullable=False, server_default=func.now())


class WeatherForecastsClass(BASE):
    """
    Base class for the External weather forecast readings
    """

    __tablename__ = WEATHER_FORECAST_TABLE_NAME

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(
        Integer,
        nullable=False,
    )

    timestamp = Column(DateTime, nullable=False, index=True)
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
