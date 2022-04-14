from app.sensors import blueprint
from flask import request, render_template
from flask_login import login_required

from sqlalchemy import and_, asc, desc

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass,
    TypeClass,
    SensorLocationClass,
    LocationClass,
)

from __app__.crop.constants import CONST_MAX_RECORDS

from utilities.utils import query_result_to_array

CONST_ACTION_ADD = "Add"
CONST_ACTION_EDIT = "Edit"

CONST_FORM_ACTION_SUBMIT = "submit"
CONST_FORM_ACTION_CANCEL = "cancel"
CONST_FORM_ACTION_DELETE = "delete"


@blueprint.route("/<template>", methods=["POST", "GET"])
@login_required
def route_template(template):
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

    return render_template(template + ".html", sensors=sensors_arr)
