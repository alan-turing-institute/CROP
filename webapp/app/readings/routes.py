"""
Module for sensor data.
"""

from flask import render_template, request
from flask_login import login_required
from sqlalchemy import and_, desc

from app.readings import blueprint
from utilities.utils import query_result_to_array

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass, 
    ReadingsAdvanticsysClass,
    ReadingsEnergyClass,
)
from __app__.crop.constants import CONST_MAX_RECORDS

@blueprint.route("/<template>")
@login_required
def route_template(template):
    """
    Main method to render templates.
    """

    if template == "advanticsys":
        if request.method == "GET":
            
            # TODO: check which sensor type data to visualise
            query = (
                db.session.query(
                    ReadingsAdvanticsysClass.timestamp,
                    SensorClass.id,
                    ReadingsAdvanticsysClass.temperature,
                    ReadingsAdvanticsysClass.humidity,
                    ReadingsAdvanticsysClass.co2,
                    ReadingsAdvanticsysClass.time_created,
                    ReadingsAdvanticsysClass.time_updated,
                )
                .filter(and_(ReadingsAdvanticsysClass.sensor_id == SensorClass.id,))
                .order_by(desc(ReadingsAdvanticsysClass.timestamp))
                .limit(CONST_MAX_RECORDS)
            )

            readings = db.session.execute(query).fetchall()

            results_arr = query_result_to_array(readings, date_iso=False)

            return render_template(template + ".html", readings=results_arr)
        else:
            return None

    elif template == "energy":

        if request.method == "GET":
            
            query = (
                db.session.query(
                    ReadingsEnergyClass.timestamp,
                    SensorClass.id,
                    ReadingsEnergyClass.electricity_consumption,
                    ReadingsEnergyClass.time_created,
                )
                .filter(and_(ReadingsEnergyClass.sensor_id == SensorClass.id,))
                .order_by(desc(ReadingsEnergyClass.timestamp))
                .limit(CONST_MAX_RECORDS)
            )

            
            readings = db.session.execute(query).fetchall()

            results_arr = query_result_to_array(readings, date_iso=False)

            return render_template(template + ".html", readings=results_arr)

        else:
            return None
    

    return None
