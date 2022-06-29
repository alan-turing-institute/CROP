from datetime import datetime

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
            SensorClass.aranet_pro_id,
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


def get_existing_sensors():
    query = (
        db.session.query(
            SensorClass.id,
            SensorClass.aranet_code,
            SensorClass.aranet_pro_id,
            SensorClass.name,
            TypeClass.sensor_type,
        )
        .filter(SensorClass.type_id == TypeClass.id)
        .order_by(asc(SensorClass.id))
        .limit(CONST_MAX_RECORDS)
    )
    sensors = db.session.execute(query).fetchall()
    sensors_arr = query_result_to_array(sensors, date_iso=False)
    return sensors_arr


def update_sensor_attributes(request):
    """Update the row in the `sensors` table according to the attributes in the form
    submission in `request`.
    """
    session = db.session
    sensor_obj = session.execute(
        session.query(SensorClass).filter_by(id=request.values["query"])
    ).scalar_one()

    for attr in (
        "type_id",
        "name",
        "device_id",
        "aranet_code",
        "aranet_pro_id",
        "serial_number",
    ):
        if attr not in request.values:
            continue
        val = request.values[attr]
        # TODO This is a bit of a strange workaround for the fact that the form will
        # always return a string. If we try to set a field to be "None" or "", a null
        # value will be set instead.
        if val == "None" or val == "":
            val = None
        setattr(sensor_obj, attr, val)
    session.commit()
    return None


def add_sensor_location(request):
    sensor_location_obj = SensorLocationClass(
        sensor_id=request.values.get("query"),
        location_id=request.values.get("location_id"),
        installation_date=request.values.get("installation_date"),
    )
    db.session.add(sensor_location_obj)
    db.session.commit()
    return None


@blueprint.route("/sensor_form", methods=["POST", "GET"])
@login_required
def sensor_form():
    if request.method == "POST":
        form_name = request.values.get("form_name")
        if form_name == "attributes_form":
            update_sensor_attributes(request)
        elif form_name == "add_location_form":
            add_sensor_location(request)

    sensors_arr = get_existing_sensors()
    sensor_id = request.args.get("query")
    if sensor_id is None:
        return render_template(
            "sensor_form.html",
            sensors=sensors_arr,
            sensor=None,
            sensor_locations=None,
            sensor_id=None,
            locs=None,
            sensor_types=None,
            latest_installation_date=None,
            latest_location=None,
        )

    if sensor_id is None:
        raise ValueError("Need a sensor ID to show the edit form for, got None.")

    # Getting selected sensor
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

    # Getting all possible sensor locations
    query = db.session.query(
        LocationClass.id,
        LocationClass.zone,
        LocationClass.aisle,
        LocationClass.column,
        LocationClass.shelf,
    ).limit(CONST_MAX_RECORDS)
    locs = db.session.execute(query).fetchall()
    locs_arr = query_result_to_array(locs, date_iso=False)
    locs_arr = sorted(
        locs_arr,
        key=lambda x: "".join(
            [str(x[k]) for k in ("zone", "aisle", "column", "shelf")]
        ),
    )

    # Getting all possible sensor types
    query = db.session.query(
        TypeClass.id,
        TypeClass.sensor_type,
    ).limit(CONST_MAX_RECORDS)
    sensor_types = db.session.execute(query).fetchall()
    sensor_types_arr = query_result_to_array(sensor_types, date_iso=False)

    # Find the latest installation date.
    if sensors_locs_arr:
        latest_installation = max(
            sensors_locs_arr, key=lambda x: x["installation_date"]
        )
        latest_installation_date = latest_installation["installation_date"]
        latest_location = latest_installation["location_id"]
    else:
        latest_installation_date = datetime(year=2020, month=1, day=1)
        latest_location = None
    latest_installation_date = latest_installation_date.date()

    return render_template(
        "sensor_form.html",
        sensors=sensors_arr,
        sensor=sensor,
        sensor_locations=sensors_locs_arr,
        sensor_id=sensor_id,
        locs=locs_arr,
        sensor_types=sensor_types_arr,
        latest_installation_date=latest_installation_date,
        latest_location=latest_location,
    )
