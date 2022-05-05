"""
Module for sensor data.
"""

from flask import render_template, request
from flask_login import login_required
from sqlalchemy import and_, desc

from app.readings import blueprint
from utilities.utils import (
    query_result_to_array,
    parse_date_range_argument,
    download_csv
)

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass,
    ReadingsAdvanticsysClass,
    ReadingsEnergyClass,
    TypeClass,
    ReadingsZensieTRHClass,
    DailyHarvestClass,
)
from __app__.crop.constants import CONST_MAX_RECORDS
import sys


@blueprint.route("/<template>", methods=["GET","POST"])
@login_required
def route_template(template):
    """
    Main method to render templates.
    """

    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    if template in ["advanticsys", "energy", "zensie_trh", "dailyharvest"]:
        if template == "advanticsys":

            query = (
                db.session.query(
                    ReadingsAdvanticsysClass.timestamp,
                    SensorClass.id,
                    SensorClass.name,
                    ReadingsAdvanticsysClass.temperature,
                    ReadingsAdvanticsysClass.humidity,
                    ReadingsAdvanticsysClass.co2,
                    ReadingsAdvanticsysClass.time_created,
                    ReadingsAdvanticsysClass.time_updated,
                    ReadingsAdvanticsysClass.sensor_id,
                )
                .filter(
                    and_(
                        ReadingsAdvanticsysClass.sensor_id
                        == SensorClass.id,
                        ReadingsAdvanticsysClass.timestamp >= dt_from,
                        ReadingsAdvanticsysClass.timestamp <= dt_to,
                    )
                )
                .order_by(desc(ReadingsAdvanticsysClass.timestamp))
                .limit(CONST_MAX_RECORDS)
            )

        elif template == "energy":

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

        elif template == "zensie_trh":

            query = (
                db.session.query(
                    ReadingsZensieTRHClass.timestamp,
                    SensorClass.name,
                    ReadingsZensieTRHClass.temperature,
                    ReadingsZensieTRHClass.humidity,
                    ReadingsZensieTRHClass.time_created,
                    ReadingsZensieTRHClass.time_updated,
                    ReadingsZensieTRHClass.sensor_id,
                )
                .filter(
                    and_(
                        ReadingsZensieTRHClass.sensor_id == SensorClass.id,
                        ReadingsZensieTRHClass.timestamp >= dt_from,
                        ReadingsZensieTRHClass.timestamp <= dt_to,
                    )
                )
                .order_by(desc(ReadingsZensieTRHClass.timestamp))
                .limit(CONST_MAX_RECORDS)
            )

        elif template == "dailyharvest":
            query = db.session.query(
                DailyHarvestClass.crop,
                DailyHarvestClass.propagation_date,
                DailyHarvestClass.location_id,
                DailyHarvestClass.stack,
                DailyHarvestClass.total_yield_weight,
                DailyHarvestClass.disease_trays,
                DailyHarvestClass.defect_trays,
                DailyHarvestClass.notes,
                DailyHarvestClass.user,
                DailyHarvestClass.time_created,
            ).limit(CONST_MAX_RECORDS)

        readings = db.session.execute(query).fetchall()
        # print(readings, file=sys.stderr)

        results_arr = query_result_to_array(readings, date_iso=False)
    if request.method == "POST":
        return download_csv(readings, template)
    else:
        return render_template(
            template + ".html",
            readings=results_arr,
            dt_from=dt_from.strftime("%B %d, %Y"),
            dt_to=dt_to.strftime("%B %d, %Y"),
            num_records = CONST_MAX_RECORDS
        )
