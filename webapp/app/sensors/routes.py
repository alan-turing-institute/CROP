from app.sensors import blueprint
from flask import request, render_template
from flask_login import login_required

from sqlalchemy import and_, asc, desc

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass, TypeClass, SensorLocationClass, LocationClass
)

from __app__.crop.constants import CONST_MAX_RECORDS

from utilities.utils import (
    query_result_to_array,
)

CONST_ACTION_ADD = "Add"
CONST_ACTION_EDIT = "Edit"

CONST_FORM_ACTION_SUBMIT = "submit"
CONST_FORM_ACTION_CANCEL = "cancel"
CONST_FORM_ACTION_DELETE = "delete"


@blueprint.route('/<template>', methods=['POST', 'GET'])
@login_required
def route_template(template):
    
    if template == "sensors":

        query = (
            db.session.query(
                SensorClass.id,
                SensorClass.device_id,
                SensorClass.name,
                SensorClass.last_updated,
                TypeClass.sensor_type,
            )
            .filter(
                and_(
                    SensorClass.type_id == TypeClass.id,
                )
            )
            .order_by(asc(SensorClass.id))
            .limit(CONST_MAX_RECORDS)
        )

        sensors = db.session.execute(query).fetchall()

        sensors_arr = query_result_to_array(sensors, date_iso=False)

        return render_template(template + '.html', sensors=sensors_arr)

    elif template == "sensor_form":

        if request.method == 'GET':

            sensor_id = request.args.get('query')

            if sensor_id is not None:

                action = CONST_ACTION_EDIT

                # Getting sensor
                query = (
                    db.session.query(
                        SensorClass.id,
                        SensorClass.device_id,
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
                print(sensors_locs_arr)
            else:
                action = CONST_ACTION_ADD
                sensor = None
                sensors_locs_arr = None

            return render_template(template + '.html', action=action, sensor=sensor, sensor_locations=sensors_locs_arr, sensor_id=sensor_id)
