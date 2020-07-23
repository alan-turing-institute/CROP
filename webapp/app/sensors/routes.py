from app.sensors import blueprint
from flask import request, render_template
from flask_login import login_required

from sqlalchemy import and_, asc

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import SensorClass, TypeClass

from __app__.crop.constants import CONST_MAX_RECORDS

from utilities.utils import (
    query_result_to_array,
)

@blueprint.route('/<template>', methods=['POST', 'GET'])
@login_required
def route_template(template):
    
    if template == "sensors":

        query = (
            db.session.query(
                SensorClass.id,
                SensorClass.device_id,
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

    # elif template == "sensor_form":

    #     if request.method == 'GET':

    #         sensor_id = request.args.get('query')
