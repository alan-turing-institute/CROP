"""
Module for sensor data.
"""

from flask import render_template, request
from flask_login import login_required
import pandas as pd
from sqlalchemy import and_, desc

from app.readings import blueprint
from core.constants import CONST_MAX_RECORDS
from core import queries
from core.structure import SQLA as db
from core.structure import (
    SensorClass,
    ReadingsEnergyClass,
    TypeClass,
    ReadingsAranetTRHClass,
    ReadingsAranetCO2Class,
    ReadingsAranetAirVelocityClass,
)
from core.utils import (
    query_result_to_array,
    parse_date_range_argument,
    download_csv,
)


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
                    ReadingsEnergyClass.electricity_consumption,
                    ReadingsEnergyClass.time_created,
                    SensorClass.id,
                    SensorClass.name,
                    TypeClass.sensor_type,
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

            trh_query = queries.trh_data_with_vpd_query(db.session).subquery()
            query = (
                db.session.query(
                    trh_query.c.timestamp,
                    trh_query.c.temperature,
                    trh_query.c.humidity,
                    trh_query.c.vpd,
                    trh_query.c.time_created,
                    trh_query.c.time_updated,
                    trh_query.c.sensor_id,
                    SensorClass.name,
                )
                .filter(
                    and_(
                        trh_query.c.sensor_id == SensorClass.id,
                        trh_query.c.timestamp >= dt_from,
                        trh_query.c.timestamp <= dt_to,
                    )
                )
                .order_by(desc(trh_query.c.timestamp))
                .limit(CONST_MAX_RECORDS)
            )
        elif template == "aranet_co2":

            query = (
                db.session.query(
                    ReadingsAranetCO2Class.timestamp,
                    ReadingsAranetCO2Class.co2,
                    ReadingsAranetCO2Class.time_created,
                    ReadingsAranetCO2Class.time_updated,
                    ReadingsAranetCO2Class.sensor_id,
                    SensorClass.name,
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
                    ReadingsAranetAirVelocityClass.current,
                    ReadingsAranetAirVelocityClass.air_velocity,
                    ReadingsAranetAirVelocityClass.time_created,
                    ReadingsAranetAirVelocityClass.time_updated,
                    ReadingsAranetAirVelocityClass.sensor_id,
                    SensorClass.name,
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

        df = pd.read_sql(query.statement, query.session.bind)
        if template == "aranet_trh":
            # Rounding to two decimal places, because our precision isn't infinite, and
            # long floats look really ugly on the front end.
            df.loc[:, "vpd"] = df.loc[:, "vpd"].round(2)
        results_arr = df.to_dict("records")

    if request.method == "POST":
        return download_csv(results_arr, template)
    else:
        return render_template(
            template + ".html",
            readings=results_arr,
            dt_from=dt_from.strftime("%B %d, %Y"),
            dt_to=dt_to.strftime("%B %d, %Y"),
            num_records=CONST_MAX_RECORDS,
        )
