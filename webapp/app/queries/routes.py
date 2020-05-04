"""
Module (routes.py) to handle queries from the 3d model javascript application
"""


from sqlalchemy import func, and_, desc
from flask_login import login_required

from app.queries import blueprint
from utilities.utils import jasonify_query_result

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorLocationClass,
    TypeClass,
    SensorClass,
    LocationClass,
    ReadingsAdvanticsysClass,
)


@blueprint.route("/getallsensors", methods=["GET"])
@login_required
def get_all_sensors():
    """
    Produces a JSON list with sensors and their latest locations.

    Returns:
        result - JSON string
    """

    # Getting the latest locations of all sensors
    sensor_temp = (
        db.session.query(
            SensorLocationClass.sensor_id,
            func.max(SensorLocationClass.installation_date).label("installation_date"),
        )
        .group_by(SensorLocationClass.sensor_id)
        .subquery()
    )

    # Collecting the general information about the selected sensors
    query = db.session.query(
        SensorLocationClass.sensor_id,
        SensorLocationClass.installation_date,
        TypeClass.sensor_type,
        LocationClass.zone,
        LocationClass.aisle,
        LocationClass.column,
        LocationClass.shelf,
    ).filter(
        and_(
            sensor_temp.c.sensor_id == SensorLocationClass.sensor_id,
            sensor_temp.c.installation_date == SensorLocationClass.installation_date,
            sensor_temp.c.sensor_id == SensorClass.id,
            SensorClass.type_id == TypeClass.id,
            SensorLocationClass.location_id == LocationClass.id,
        )
    )

    execute_result = db.session.execute(query).fetchall()
    result = jasonify_query_result(execute_result)

    return result


@blueprint.route("/getadvanticsysdata/<sensor_id>", methods=["GET"])
@login_required
def get_advanticsys_data(sensor_id):
    """
    Produces a JSON with the Advanticsys sensor data for a specified sensor.

    Args:
        sensor_id - Advanticsys sensor ID
    Returns:
        result - JSON string
    """

    query = (
        db.session.query(
            SensorClass.id,
            ReadingsAdvanticsysClass.timestamp,
            ReadingsAdvanticsysClass.temperature,
            ReadingsAdvanticsysClass.humidity,
            ReadingsAdvanticsysClass.co2,
            ReadingsAdvanticsysClass.time_created,
            ReadingsAdvanticsysClass.time_updated,
        )
        .filter(
            and_(
                SensorClass.id == sensor_id,
                ReadingsAdvanticsysClass.sensor_id == SensorClass.id,
            )
        )
        .order_by(desc(ReadingsAdvanticsysClass.timestamp))
    )

    execute_result = db.session.execute(query).fetchall()
    result = jasonify_query_result(execute_result)

    return result
