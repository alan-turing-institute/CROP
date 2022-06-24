from flask import request, render_template
from flask_login import login_required
from sqlalchemy import and_, asc, desc

from __app__.crop.constants import CONST_MAX_RECORDS
from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass,
    TypeClass,
    SensorLocationClass,
    LocationClass,
)
from app.sensors import blueprint
from utilities.utils import query_result_to_array


@blueprint.route("/sensor_list", methods=["POST", "GET"])
@login_required
def sensor_list():
    query = (
        db.session.query(
            SensorClass.id,
            SensorClass.aranet_code,
            SensorClass.name,
            TypeClass.sensor_type,
            SensorLocationClass.sensor_id,
            SensorLocationClass.location_id,
            SensorLocationClass.installation_date,
            LocationClass.id.label("location_id"),
            LocationClass.zone,
            LocationClass.aisle,
            LocationClass.column,
            LocationClass.shelf,
        )
        .filter(SensorClass.type_id == TypeClass.id)
        .join(
            SensorLocationClass,
            SensorClass.id == SensorLocationClass.sensor_id,
            isouter=True,
        )
        .join(
            LocationClass,
            LocationClass.id == SensorLocationClass.location_id,
            isouter=True,
        )
        .order_by(asc(SensorClass.id))
        .limit(CONST_MAX_RECORDS)
    )

    sensors = db.session.execute(query).fetchall()

    sensors_arr = query_result_to_array(sensors, date_iso=False)

    return render_template("sensor_list.html", sensors=sensors_arr)


@blueprint.route("/sensor_form", methods=["POST", "GET"])
@login_required
def sensor_form():
    if request.method == "GET":
        sensor_id = request.args.get("query")
        if sensor_id is None:
            raise ValueError("Need a sensor ID to show the edit form for, got None.")

        # Getting sensor
        query = (
            db.session.query(
                SensorClass.id,
                SensorClass.device_id,
                SensorClass.aranet_code,
                SensorClass.aranet_pro_id,
                SensorClass.serial_number,
                SensorClass.type_id,
                SensorClass.name,
                SensorClass.last_updated,
                TypeClass.sensor_type,
            )
            .filter(
                and_(
                    SensorClass.id == sensor_id,
                    SensorClass.type_id == TypeClass.id,
                )
            )
            .order_by(asc(SensorClass.id))
            .limit(1)
        )
        sensors = db.session.execute(query).fetchall()
        sensor_arr = query_result_to_array(sensors, date_iso=False)
        if len(sensor_arr) > 0:
            sensor = sensor_arr[0]
        else:
            sensor = sensor_arr

        # Getting sensor locations
        query = (
            db.session.query(
                SensorLocationClass.id,
                SensorLocationClass.sensor_id,
                SensorLocationClass.location_id,
                SensorLocationClass.installation_date,
                LocationClass.zone,
                LocationClass.aisle,
                LocationClass.column,
                LocationClass.shelf,
            )
            .filter(
                and_(
                    SensorLocationClass.sensor_id == sensor_id,
                    LocationClass.id == SensorLocationClass.location_id,
                )
            )
            .order_by(asc(SensorLocationClass.installation_date))
            .limit(CONST_MAX_RECORDS)
        )
        sensors_locs = db.session.execute(query).fetchall()
        sensors_locs_arr = query_result_to_array(sensors_locs, date_iso=False)
        return render_template(
            "sensor_form.html",
            sensor=sensor,
            sensor_locations=sensors_locs_arr,
            sensor_id=sensor_id,
        )
