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
)

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass,
    ReadingsAdvanticsysClass,
    ReadingsEnergyClass,
    TypeClass,
    ReadingsZensieTRHClass,
    CropGrowthClass,
)
from __app__.crop.constants import CONST_MAX_RECORDS


@blueprint.route("/<template>", methods=["GET"])
@login_required
def route_template(template):
    """
    Main method to render templates.
    """

    if request.method == "GET":

        dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

        if template in ["advanticsys", "energy", "zensie_trh", "cropgrowth"]:
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
                    )
                    .filter(
                        and_(
                            ReadingsAdvanticsysClass.sensor_id == SensorClass.id,
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
                        SensorClass.id,
                        SensorClass.name,
                        ReadingsZensieTRHClass.temperature,
                        ReadingsZensieTRHClass.humidity,
                        ReadingsZensieTRHClass.time_created,
                        ReadingsZensieTRHClass.time_updated,
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

            elif template == "cropgrowth":
                query = (
                    db.session.query(
                        CropGrowthClass.crop,
                        CropGrowthClass.harvest_date,
                        CropGrowthClass.time_created,
                        CropGrowthClass.time_updated,
                    )
                    .filter(
                        and_(
                            # ReadingsZensieTRHClass.sensor_id == SensorClass.id,
                            CropGrowthClass.timestamp >= dt_from,
                            CropGrowthClass.timestamp <= dt_to,
                        )
                    )
                    .order_by(desc(CropGrowthClass.harvest_date))
                    .limit(CONST_MAX_RECORDS)
                )

            readings = db.session.execute(query).fetchall()

            results_arr = query_result_to_array(readings, date_iso=False)

            return render_template(
                template + ".html",
                readings=results_arr,
                dt_from=dt_from.strftime("%B %d, %Y"),
                dt_to=dt_to.strftime("%B %d, %Y"),
            )

    return None
