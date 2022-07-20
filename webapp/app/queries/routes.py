"""
Module (routes.py) to handle queries from the 3d model javascript application
"""

from flask import request
from flask_login import login_required
from sqlalchemy import func, and_, desc

from app.queries import blueprint

from utilities.utils import (
    filter_latest_sensor_location,
    jasonify_query_result,
    parse_date_range_argument,
)

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorLocationClass,
    TypeClass,
    SensorClass,
    LocationClass,
    ReadingsAdvanticsysClass,
    ReadingsEnergyClass,
    ReadingsAranetTRHClass,
    ReadingsAranetCO2Class,
    ReadingsAranetAirVelocityClass,
    ReadingsWeatherClass,
)


@blueprint.route("/getallsensors", methods=["GET"])
# @login_required
def get_all_sensors():
    """
    Produces a JSON list with sensors and their latest locations.

    Returns:
        result - JSON string
    """
    # Collecting the general information about the selected sensors
    query = db.session.query(
        SensorLocationClass.sensor_id,
        SensorLocationClass.installation_date,
        TypeClass.sensor_type,
        LocationClass.zone,
        LocationClass.aisle,
        LocationClass.column,
        LocationClass.shelf,
        SensorClass.aranet_code,
        SensorClass.aranet_pro_id,
        SensorClass.serial_number,
    ).filter(
        and_(
            filter_latest_sensor_location(db),
            SensorClass.type_id == TypeClass.id,
            SensorLocationClass.location_id == LocationClass.id,
            SensorLocationClass.sensor_id == SensorClass.id,
        )
    )

    execute_result = db.session.execute(query).fetchall()

    result = jasonify_query_result(execute_result)

    return result


@blueprint.route("/getadvanticsysdata/<sensor_id>", methods=["GET"])
# @login_required
def get_advanticsys_data(sensor_id):
    """
    Produces a JSON with the Advanticsys sensor data for a specified sensor.

    Args:
        sensor_id - Advanticsys sensor ID
    Returns:
        result - JSON string
    """

    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    query = (
        db.session.query(
            ReadingsAdvanticsysClass.sensor_id,
            ReadingsAdvanticsysClass.timestamp,
            ReadingsAdvanticsysClass.temperature,
            ReadingsAdvanticsysClass.humidity,
            ReadingsAdvanticsysClass.co2,
            ReadingsAdvanticsysClass.time_created,
            ReadingsAdvanticsysClass.time_updated,
        )
        .filter(
            and_(
                ReadingsAdvanticsysClass.sensor_id == sensor_id,
                ReadingsAdvanticsysClass.timestamp >= dt_from,
                ReadingsAdvanticsysClass.timestamp <= dt_to,
            )
        )
        .order_by(desc(ReadingsAdvanticsysClass.timestamp))
    )

    execute_result = db.session.execute(query).fetchall()
    result = jasonify_query_result(execute_result)

    return result


@blueprint.route("/getstarkdata/<sensor_id>", methods=["GET"])
# @login_required
def get_stark_data(sensor_id):
    """
    Produces a JSON with Stark readings data for a specified sensor (meter).

    Args:
        sensor_id - Stark meter ID
    Returns:
        result - JSON string
    """

    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    query = (
        db.session.query(
            ReadingsEnergyClass.sensor_id,
            ReadingsEnergyClass.timestamp,
            ReadingsEnergyClass.electricity_consumption,
            ReadingsEnergyClass.time_created,
            ReadingsEnergyClass.time_updated,
        )
        .filter(
            and_(
                ReadingsEnergyClass.sensor_id == sensor_id,
                ReadingsEnergyClass.timestamp >= dt_from,
                ReadingsEnergyClass.timestamp <= dt_to,
            )
        )
        .order_by(desc(ReadingsEnergyClass.timestamp))
    )

    execute_result = db.session.execute(query).fetchall()
    result = jasonify_query_result(execute_result)

    return result


@blueprint.route("/getaranettrhdata/<sensor_id>", methods=["GET"])
# @login_required
def get_aranet_trh_data(sensor_id):
    """
    Produces a JSON with the Aranet Temperature and Relative Humidity
    data for a specified sensor.

    Args:
        sensor_id - sensor ID as stored in CROP db (int).
    Returns:
        result - JSON string
    """

    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    query = (
        db.session.query(
            ReadingsAranetTRHClass.sensor_id,
            ReadingsAranetTRHClass.timestamp,
            ReadingsAranetTRHClass.temperature,
            ReadingsAranetTRHClass.humidity,
            ReadingsAranetTRHClass.time_created,
            ReadingsAranetTRHClass.time_updated,
        )
        .filter(
            and_(
                ReadingsAranetTRHClass.sensor_id == sensor_id,
                ReadingsAranetTRHClass.timestamp >= dt_from,
                ReadingsAranetTRHClass.timestamp <= dt_to,
            )
        )
        .order_by(desc(ReadingsAranetTRHClass.timestamp))
    )

    execute_result = db.session.execute(query).fetchall()
    result = jasonify_query_result(execute_result)

    return result


@blueprint.route("/getaranetco2data/<sensor_id>", methods=["GET"])
# @login_required
def get_aranet_co2_data(sensor_id):
    """
    Produces a JSON with the Aranet CO2
    data for a specified sensor.

    Args:
        sensor_id - sensor ID as stored in CROP db (int).
    Returns:
        result - JSON string
    """

    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    query = (
        db.session.query(
            ReadingsAranetCO2Class.sensor_id,
            ReadingsAranetCO2Class.timestamp,
            ReadingsAranetCO2Class.co2,
            ReadingsAranetCO2Class.time_created,
            ReadingsAranetCO2Class.time_updated,
        )
        .filter(
            and_(
                ReadingsAranetCO2Class.sensor_id == sensor_id,
                ReadingsAranetCO2Class.timestamp >= dt_from,
                ReadingsAranetCO2Class.timestamp <= dt_to,
            )
        )
        .order_by(desc(ReadingsAranetCO2Class.timestamp))
    )

    execute_result = db.session.execute(query).fetchall()
    result = jasonify_query_result(execute_result)

    return result


@blueprint.route("/getaranetairvelocitydata/<sensor_id>", methods=["GET"])
# @login_required
def get_aranet_airvelocity_data(sensor_id):
    """
    Produces a JSON with the Aranet air velocity
    data for a specified sensor.

    Args:
        sensor_id - sensor ID as stored in CROP db (int).
    Returns:
        result - JSON string
    """

    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    query = (
        db.session.query(
            ReadingsAranetAirVelocityClass.sensor_id,
            ReadingsAranetAirVelocityClass.timestamp,
            ReadingsAranetAirVelocityClass.current,
            ReadingsAranetAirVelocityClass.air_velocity,
            ReadingsAranetAirVelocityClass.time_created,
            ReadingsAranetAirVelocityClass.time_updated,
        )
        .filter(
            and_(
                ReadingsAranetAirVelocityClass.sensor_id == sensor_id,
                ReadingsAranetAirVelocityClass.timestamp >= dt_from,
                ReadingsAranetAirVelocityClass.timestamp <= dt_to,
            )
        )
        .order_by(desc(ReadingsAranetAirVelocityClass.timestamp))
    )

    execute_result = db.session.execute(query).fetchall()
    result = jasonify_query_result(execute_result)
    return result



@blueprint.route("/getweatherdata", methods=["GET"])
# @login_required
def get_weather():
    """
    Produces a JSON with weather data.

    Returns:
        result - JSON string
    """

    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    query = (
        db.session.query(
            ReadingsWeatherClass.temperature,
            ReadingsWeatherClass.relative_humidity,
            ReadingsWeatherClass.wind_speed,
            ReadingsWeatherClass.wind_direction,
            ReadingsWeatherClass.rain,
            ReadingsWeatherClass.air_pressure,
            ReadingsWeatherClass.timestamp,
            ReadingsWeatherClass.icon,
        )
        .filter(
            and_(
                ReadingsWeatherClass.timestamp >= dt_from,
                ReadingsWeatherClass.timestamp <= dt_to,
            )
        )
        .order_by(desc(ReadingsWeatherClass.timestamp))
    )

    execute_result = db.session.execute(query).fetchall()
    result = jasonify_query_result(execute_result)

    return result

@blueprint.route("/croptypes", methods=["GET"])
def get_crop_types():
    """
    Get a list of types of crop, and some of their properties.
    """
    query = (
        db.session.query(
            CropTypeClass.id,
            CropTypeClass.growapp_id,
            CropTypeClass.name,
            CropTypeClass.seed_density,
            CropTypeClass.propagation_period,
            CropTypeClass.grow_period,
            CropTypeClass.is_pre_harvest
        )
    )
    execute_result = db.session.execute(query).fetchall()
    result = jasonify_query_result(execute_result)
    return result


@blueprint.route("/batches", methods=["GET"])
def get_all_batches():
    """
    Get the full list of static data on all batches in the database.
    """
    query = (
        db.session.query(
            BatchClass.id,
            BatchClass.growapp_id,
            BatchClass.crop_type_id,
            BatchClass.tray_size,
            BatchClass.number_of_trays
        )
    )
    execute_result = db.session.execute(query).fetchall()
    result = jasonify_query_result(execute_result)
    return result


@blueprint.route("/batches/<batch_id>", methods=["GET"])
def get_batch_details(batch_id):
    """
    Get all information, including 'events', for a given batch.
    """
    static_data_query = (
        db.session.query(
            BatchClass.id,
            BatchClass.growapp_id,
            BatchClass.crop_type_id,
            BatchClass.tray_size,
            BatchClass.number_of_trays
        ).filter(
            BatchClass.id == batch_id
        )
    )
