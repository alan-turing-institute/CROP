"""
Module (routes.py) to handle queries from the 3d model javascript application
"""
from datetime import datetime, timedelta
import json

from flask import request

# from flask_login import login_required
import pandas as pd
from sqlalchemy import and_, desc

from app.queries import blueprint
from core import queries
from core.structure import SQLA as db
from core.structure import (
    TypeClass,
    SensorClass,
    LocationClass,
    ReadingsAdvanticsysClass,
    ReadingsEnergyClass,
    ReadingsAranetTRHClass,
    ReadingsAranetCO2Class,
    ReadingsAranetAirVelocityClass,
    ReadingsWeatherClass,
    CropTypeClass,
    BatchClass,
    BatchEventClass,
    HarvestClass,
    EventType,
)
from core.queries import closest_trh_sensors, batch_list
from core.utils import (
    query_result_to_array,
    jsonify_query_result,
    parse_date_range_argument,
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
    locations_query = queries.latest_sensor_locations(db.session).subquery()
    query = db.session.query(
        locations_query.c.sensor_id,
        locations_query.c.installation_date,
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
            SensorClass.type_id == TypeClass.id,
            locations_query.c.location_id == LocationClass.id,
            locations_query.c.sensor_id == SensorClass.id,
        )
    )

    execute_result = db.session.execute(query).fetchall()

    result = jsonify_query_result(execute_result)

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
    result = jsonify_query_result(execute_result)

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
    result = jsonify_query_result(execute_result)

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
    result = jsonify_query_result(execute_result)

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
    result = jsonify_query_result(execute_result)

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
    result = jsonify_query_result(execute_result)
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
    result = jsonify_query_result(execute_result)
    return result


@blueprint.route("/croptypes", methods=["GET"])
def get_crop_types():
    """
    Get a list of types of crop, and some of their properties.
    """
    query = db.session.query(
        CropTypeClass.id,
        CropTypeClass.growapp_id,
        CropTypeClass.name,
        CropTypeClass.seed_density,
        CropTypeClass.propagation_period,
        CropTypeClass.grow_period,
        CropTypeClass.is_pre_harvest,
    )
    execute_result = db.session.execute(query).fetchall()
    result = jsonify_query_result(execute_result)
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
            CropTypeClass.name,
            BatchClass.tray_size,
            BatchClass.number_of_trays,
        )
    ).filter(CropTypeClass.id == BatchClass.crop_type_id)
    execute_result = db.session.execute(query).fetchall()
    result = jsonify_query_result(execute_result)
    return result


@blueprint.route("/batches/<batch_id>", methods=["GET"])
def get_batch_details(batch_id):
    """
    Get all information, including 'events', for a given batch.
    """
    query = db.session.query(
        BatchClass.id,
        BatchClass.growapp_id,
        CropTypeClass.name,
        BatchClass.tray_size,
        BatchClass.number_of_trays,
    ).filter(
        and_(BatchClass.id == batch_id, CropTypeClass.id == BatchClass.crop_type_id)
    )
    execute_result = db.session.execute(query).fetchall()
    result = jsonify_query_result(execute_result)
    return result


@blueprint.route("/batchevents", methods=["GET"])
def get_all_batchevents():
    """
    Get all batch events.
    """

    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    query = db.session.query(
        BatchEventClass.id,
        BatchEventClass.growapp_id,
        BatchEventClass.event_type,
        BatchEventClass.event_time,
        BatchEventClass.next_action_time,
        BatchEventClass.location_id,
    ).filter(
        and_(BatchEventClass.event_time > dt_from, BatchEventClass.event_time < dt_to)
    )
    execute_result = db.session.execute(query).fetchall()
    results_arr = query_result_to_array(execute_result)
    for r in results_arr:
        r["event_type"] = r["event_type"].name
    result = jsonify_query_result(results_arr)
    return result


@blueprint.route("/batchtransferevents", methods=["GET"])
def get_transfer_batchevents():
    """
    Get all batch events with a location (i.e. transfer events).
    """

    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    query = db.session.query(
        BatchEventClass.id,
        BatchEventClass.growapp_id,
        BatchEventClass.event_type,
        BatchEventClass.event_time,
        BatchEventClass.next_action_time,
        LocationClass.zone,
        LocationClass.aisle,
        LocationClass.column,
        LocationClass.shelf,
    ).filter(
        and_(
            LocationClass.id == BatchEventClass.location_id,
            BatchEventClass.event_time > dt_from,
            BatchEventClass.event_time < dt_to,
        )
    )
    execute_result = db.session.execute(query).fetchall()
    results_arr = query_result_to_array(execute_result)
    for r in results_arr:
        r["event_type"] = r["event_type"].name
    result = jsonify_query_result(results_arr)
    return result


@blueprint.route("/batchevents/<batch_id>", methods=["GET"])
def get_all_batchevents_for_batch(batch_id):
    """
    Get all batch events for a specific batch.
    """

    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    query = db.session.query(
        BatchEventClass.id,
        BatchEventClass.growapp_id,
        BatchEventClass.event_type,
        BatchEventClass.event_time,
        BatchEventClass.next_action_time,
        BatchEventClass.location_id,
    ).filter(
        and_(
            BatchEventClass.batch_id == batch_id,
            BatchEventClass.event_time > dt_from,
            BatchEventClass.event_time < dt_to,
        )
    )
    execute_result = db.session.execute(query).fetchall()
    results_arr = query_result_to_array(execute_result)
    for r in results_arr:
        r["event_type"] = r["event_type"].name
    result = jsonify_query_result(results_arr)
    return result


@blueprint.route("/harvests", methods=["GET"])
def get_all_harvests():
    """
    Get all harvests.
    """
    query = db.session.query(
        HarvestClass.id,
        HarvestClass.growapp_id,
        HarvestClass.crop_yield,
        HarvestClass.waste_disease,
        HarvestClass.waste_defect,
        HarvestClass.over_production,
        BatchEventClass.batch_id,
        BatchEventClass.event_time,
        BatchClass.tray_size,
        BatchClass.number_of_trays,
        CropTypeClass.name,
        LocationClass.zone,
        LocationClass.aisle,
        LocationClass.column,
        LocationClass.shelf,
    ).filter(
        and_(
            BatchEventClass.id == HarvestClass.batch_event_id,
            BatchClass.id == BatchEventClass.batch_id,
            CropTypeClass.id == BatchClass.crop_type_id,
            LocationClass.id == HarvestClass.location_id,
        )
    )
    execute_result = db.session.execute(query).fetchall()
    result = jsonify_query_result(execute_result)
    return result


@blueprint.route("/batchesinfarm", methods=["GET"])
def get_growing_batches():
    query = batch_list(db.session)
    squery = query.subquery()
    fquery = db.session.query(squery).filter(squery.c.last_event == "transfer")
    execute_result = db.session.execute(fquery).fetchall()
    result = query_result_to_array(execute_result)
    return json.dumps(result)


@blueprint.route("/shelfdata/<zone>", methods=["GET"])
def get_shelf_data_for_zone(zone):
    """
    find all shelves in a given zone, find the nearest sensor, latest
    reading from that sensor, any crop currently growing there.
    """
    #    batch_squery = batch_list(db.session).subquery()
    #    batch_query = db.session.query(batch_squery).filter(
    #        batch_squery.c.last_event == "transfer"
    #    )
    #    nearest_trh_squery = closest_trh_sensors(db.session).subquery()
    #    query = db.session.query(batch_squery).outerjoin(
    #        nearest_trh_squery,
    #        and_(
    #            nearest_trh_squery.c.location_id==batch_squery.c.location_id,
    #            batch_squery.c.zone == zone,
    #            batch_squery.c.last_event == "transfer"
    #        )
    #    )#.group_by(nearest_trh_squery.c.location_id)
    #
    #    execute_result = db.session.execute(query).fetchall()
    #    result = query_result_to_array(execute_result)
    #    df = pd.DataFrame(result)
    #    return df.to_json(orient="records")
    ##    return json.dumps(result)
    #
    #
    # def dummy():
    result = [
        {
            "zone": zone,
            "aisle": "A",
            "column": 3,
            "shelf": 2,
            "cropData": {
                "cropList": [
                    {
                        "zone": zone,
                        "aisle": "A",
                        "column": 4,
                        "shelf": 2,
                        "name": "basil",
                        "number_of_trays": 10,
                        "tray_size": 0.4,
                        "event_time": "2023-01-10",
                        "next_action_time": "2023-02-01",
                    }
                ]
            },
            "nearestSensor": {
                "sensorList": [
                    {
                        "zone": zone,
                        "aisle": "A",
                        "column": 4,
                        "shelf": 2,
                        "installation_date": "2020-01-01",
                        "sensor_id": 17,
                        "aranet_code": "a4281",
                        "serial_number": "3445230923",
                        "aranet_pro_id": "ab312",
                    }
                ]
            },
            "latestReading": {
                "readingList": [
                    {
                        "sensor_id": 17,
                        "time_created": "2022-01-11 12:00:00",
                        "time_updated": "",
                        "timestamp": "2022-01-11 12:00:00",
                        "temperature": 18.4,
                        "humidity": 68,
                    }
                ]
            },
        }
    ]
    return json.dumps(result)


@blueprint.route("/shelfdata/<zone>/<aisle>/<column>/<shelf>", methods=["GET"])
def get_shelf_data(zone, aisle, column, shelf):
    """
    for shelf in a given zone/aisle/column/shelf, find the nearest sensor,
    latest reading from that sensor, any crop currently growing there.
    """
    result = {
        "cropData": {
            "zone": zone,
            "aisle": "A",
            "column": 4,
            "shelf": 2,
            "name": "basil",
            "number_of_trays": 10,
            "tray_size": 0.4,
            "event_time": "2023-01-10",
            "next_action_time": "2023-02-01",
        },
        "sensor": {
            "zone": zone,
            "aisle": "A",
            "column": 4,
            "shelf": 2,
            "installation_date": "2020-01-01",
            "sensor_id": 17,
            "aranet_code": "a4281",
            "serial_number": "3445230923",
            "aranet_pro_id": "ab312",
        },
        "latestReading": {
            "sensor_id": 17,
            "time_created": "2022-01-11 12:00:00",
            "time_updated": "",
            "timestamp": "2022-01-11 12:00:00",
        },
    }
    return json.dumps(result)


@blueprint.route("closest_trh_sensors", methods=["GET"])
def get_closest_sensors():
    closest_trh_squery = closest_trh_sensors(db.session).subquery(
        "location_and_trh_ids"
    )
    query = db.session.query(
        LocationClass.aisle,
        LocationClass.column,
        LocationClass.shelf,
        LocationClass.id,
        closest_trh_squery.c.sensor_id,
    ).join(closest_trh_squery, closest_trh_squery.c.location_id == LocationClass.id)
    execute_result = db.session.execute(query).fetchall()
    result = query_result_to_array(execute_result)
    return json.dumps(result)
