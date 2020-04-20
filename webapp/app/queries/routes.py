"""
Module (routes.py) to handle queries from the 3d model javascript application
"""

import json
from datetime import datetime
from sqlalchemy import func, and_
from flask_login import login_required

from app.queries import blueprint

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorLocationClass,
    TypeClass,
    SensorClass,
    LocationClass,
)


@blueprint.route("/getallsensors", methods=["GET"])
@login_required
def get_all_sensors():
    """
    Produces a JSON list with sensors and their latest locations
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

    dict_entry, results_arr = {}, []
    for rowproxy in execute_result:

        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():

            if isinstance(value, datetime):
                dict_entry = {**dict_entry, **{column: value.isoformat()}}
            else:
                dict_entry = {**dict_entry, **{column: value}}
        results_arr.append(dict_entry)

    result = json.dumps(results_arr, ensure_ascii=True, indent=4, sort_keys=True)

    return result
