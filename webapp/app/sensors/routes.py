from datetime import datetime

from flask import redirect, request, render_template
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
            SensorClass.type_id,
            SensorClass.device_id,
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
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    return None


def add_sensor_location(request):
    sensor_location_obj = SensorLocationClass(
        sensor_id=request.values.get("query"),
        location_id=request.values.get("location_id"),
        installation_date=request.values.get("installation_date"),
    )
    session = db.session
    session.add(sensor_location_obj)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    return None


def create_new_sensor(request):
    new_sensor = SensorClass(
        type_id=request.values.get("new_sensor_type_id"),
        device_id=request.values.get("new_sensor_device_id"),
        name="New sensor",
    )
    session = db.session
    session.add(new_sensor)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    return new_sensor.id


def get_sensor_details(sensor_id):
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
    return sensor


def get_sensor_location_history(sensor_id):
    query = (
        db.session.query(
            SensorLocationClass.id,
            SensorLocationClass.sensor_id,
            SensorLocationClass.location_id,
            SensorLocationClass.installation_date,
            LocationClass.id,
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
    location_history = db.session.execute(query).fetchall()
    location_history_arr = query_result_to_array(location_history, date_iso=False)
    return location_history_arr


def get_possible_sensor_locations():
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
    return locs_arr


def get_possible_sensor_types():
    query = db.session.query(
        TypeClass.id,
        TypeClass.sensor_type,
    ).limit(CONST_MAX_RECORDS)
    sensor_types = db.session.execute(query).fetchall()
    sensor_types_arr = query_result_to_array(sensor_types, date_iso=False)
    return sensor_types_arr


def render_sensor_picker_page(sensors_arr, locs_arr, sensor_types_arr):
    return render_template(
        "sensor_form.html",
        sensors=sensors_arr,
        sensor=None,
        sensor_locations=None,
        sensor_id=None,
        locs=locs_arr,
        sensor_types=sensor_types_arr,
        latest_installation_date=None,
        latest_location=None,
    )


@blueprint.route("/sensor_form", methods=["POST", "GET"])
@login_required
def sensor_form():
    if request.method == "POST":
        form_name = request.values.get("form_name")
        if form_name == "attributes_form":
            update_sensor_attributes(request)
        elif form_name == "add_location_form":
            add_sensor_location(request)
        elif form_name == "create_new_form":
            new_sensor_id = create_new_sensor(request)
            return redirect(f"sensor_form?query={new_sensor_id}")

    sensors_arr = get_existing_sensors()
    locs_arr = get_possible_sensor_locations()
    sensor_types_arr = get_possible_sensor_types()
    sensor_id = request.args.get("query")
    if sensor_id is None:
        return render_sensor_picker_page(sensors_arr, locs_arr, sensor_types_arr)

    sensor = get_sensor_details(sensor_id)
    if not sensor:
        return render_sensor_picker_page(sensors_arr, locs_arr, sensor_types_arr)

    location_history_arr = get_sensor_location_history(sensor_id)

    # Find the latest installation date.
    if location_history_arr:
        latest_installation = max(
            location_history_arr, key=lambda x: x["installation_date"]
        )
        latest_installation_date = latest_installation["installation_date"]
        latest_location = latest_installation["location_id"]
    else:
        latest_installation_date = datetime(year=2020, month=1, day=1)
        latest_location = None
    latest_installation_date = latest_installation_date.date()

    # For nicer display of missing data in the web form, change any missing entries for
    # string fields in the sensor details to be the empty string instead.
    for k in ("device_id", "aranet_code", "aranet_pro_id", "serial_number", "name"):
        if sensor[k] is None:
            sensor[k] = ""

    return render_template(
        "sensor_form.html",
        sensors=sensors_arr,
        sensor=sensor,
        location_history=location_history_arr,
        sensor_id=sensor_id,
        locs=locs_arr,
        sensor_types=sensor_types_arr,
        latest_installation_date=latest_installation_date,
        latest_location=latest_location,
    )
