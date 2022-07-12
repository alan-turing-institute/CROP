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
    ReadingsZensieTRHClass,
    ReadingsAranetTRHClass,
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


@blueprint.route("/get30mhzrhtdata/<sensor_id>", methods=["GET"])
# @login_required
def get_30mhz_rht_data(sensor_id):
    """
    Produces a JSON with the 30MHz RH & T sensor data for a specified sensor.

    Args:
        sensor_id - Advanticsys sensor ID
    Returns:
        result - JSON string
    """

    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    query = (
        db.session.query(
            ReadingsZensieTRHClass.sensor_id,
            ReadingsZensieTRHClass.timestamp,
            ReadingsZensieTRHClass.temperature,
            ReadingsZensieTRHClass.humidity,
            ReadingsZensieTRHClass.time_created,
            ReadingsZensieTRHClass.time_updated,
        )
        .filter(
            and_(
                ReadingsZensieTRHClass.sensor_id == sensor_id,
                ReadingsZensieTRHClass.timestamp >= dt_from,
                ReadingsZensieTRHClass.timestamp <= dt_to,
            )
        )
        .order_by(desc(ReadingsZensieTRHClass.timestamp))
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
