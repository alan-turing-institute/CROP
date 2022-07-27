"""
Module for sensor data.
"""

import sys
from flask import render_template, request, send_file
from flask_login import login_required
from sqlalchemy import and_, desc
import pandas as pd
import io

from app.readings import blueprint
from utilities.utils import (
    query_result_to_array,
    parse_date_range_argument,
    download_csv,
)

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass,
    ReadingsEnergyClass,
    TypeClass,
    ReadingsAranetTRHClass,
    ReadingsAranetCO2Class,
    ReadingsAranetAirVelocityClass,
)
from __app__.crop.constants import CONST_MAX_RECORDS


@blueprint.route("/<template>", methods=["GET", "POST"])
@login_required
def route_template(template):
    """
    Main method to render templates.
    """

    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    if template in ["energy", "aranet_trh", "aranet_co2", "aranet_air_velocity"]:

        if template == "energy":

            query = (
                db.session.query(
                    ReadingsEnergyClass.timestamp,
                    SensorClass.id,
                    SensorClass.name,
                    TypeClass.sensor_type,
                    ReadingsEnergyClass.electricity_consumption,
                    ReadingsEnergyClass.time_created,
                )
                .filter(
                    and_(
                        SensorClass.type_id == TypeClass.id,
                        ReadingsEnergyClass.sensor_id == SensorClass.id,
                        ReadingsEnergyClass.timestamp >= dt_from,
                        ReadingsEnergyClass.timestamp <= dt_to,
                    )
                )
                .order_by(desc(ReadingsEnergyClass.timestamp))
                .limit(CONST_MAX_RECORDS)
            )

        elif template == "aranet_trh":

            query = (
                db.session.query(
                    ReadingsAranetTRHClass.timestamp,
                    SensorClass.name,
                    ReadingsAranetTRHClass.temperature,
                    ReadingsAranetTRHClass.humidity,
                    ReadingsAranetTRHClass.time_created,
                    ReadingsAranetTRHClass.time_updated,
                    ReadingsAranetTRHClass.sensor_id,
                )
                .filter(
                    and_(
                        ReadingsAranetTRHClass.sensor_id == SensorClass.id,
                        ReadingsAranetTRHClass.timestamp >= dt_from,
                        ReadingsAranetTRHClass.timestamp <= dt_to,
                    )
                )
                .order_by(desc(ReadingsAranetTRHClass.timestamp))
                .limit(CONST_MAX_RECORDS)
            )
        elif template == "aranet_co2":

            query = (
                db.session.query(
                    ReadingsAranetCO2Class.timestamp,
                    SensorClass.name,
                    ReadingsAranetCO2Class.co2,
                    ReadingsAranetCO2Class.time_created,
                    ReadingsAranetCO2Class.time_updated,
                    ReadingsAranetCO2Class.sensor_id,
                )
                .filter(
                    and_(
                        ReadingsAranetCO2Class.sensor_id == SensorClass.id,
                        ReadingsAranetCO2Class.timestamp >= dt_from,
                        ReadingsAranetCO2Class.timestamp <= dt_to,
                    )
                )
                .order_by(desc(ReadingsAranetCO2Class.timestamp))
                .limit(CONST_MAX_RECORDS)
            )
        elif template == "aranet_air_velocity":

            query = (
                db.session.query(
                    ReadingsAranetAirVelocityClass.timestamp,
                    SensorClass.name,
                    ReadingsAranetAirVelocityClass.current,
                    ReadingsAranetAirVelocityClass.air_velocity,
                    ReadingsAranetAirVelocityClass.time_created,
                    ReadingsAranetAirVelocityClass.time_updated,
                    ReadingsAranetAirVelocityClass.sensor_id,
                )
                .filter(
                    and_(
                        ReadingsAranetAirVelocityClass.sensor_id == SensorClass.id,
                        ReadingsAranetAirVelocityClass.timestamp >= dt_from,
                        ReadingsAranetAirVelocityClass.timestamp <= dt_to,
                    )
                )
                .order_by(desc(ReadingsAranetAirVelocityClass.timestamp))
                .limit(CONST_MAX_RECORDS)
            )



        readings = db.session.execute(query).fetchall()

        results_arr = query_result_to_array(readings, date_iso=False)
    if request.method == "POST":
        return download_csv(readings, template)
    else:
        return render_template(
            template + ".html",
            readings=results_arr,
            dt_from=dt_from.strftime("%B %d, %Y"),
            dt_to=dt_to.strftime("%B %d, %Y"),
            num_records=CONST_MAX_RECORDS,
        )
