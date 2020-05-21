"""
Analysis dashboards module.
"""

import pandas as pd

from flask_login import login_required
from flask import render_template, request
from sqlalchemy import and_, desc

from app.home import blueprint

from utilities.utils import (
    parse_date_range_argument,
)

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass,
    ReadingsAdvanticsysClass,
    ReadingsEnergyClass,
)
from __app__.crop.constants import CONST_MAX_RECORDS



@blueprint.route("/index")
@login_required
def index():
    """
    Index page
    """
    return render_template("index.html")


@blueprint.route("/<template>")
@login_required
def route_template(template):
    """
    Renders templates
    """

    if template == "dashboard":

        dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

        query = (
                    db.session.query(
                        ReadingsAdvanticsysClass.timestamp,
                        ReadingsAdvanticsysClass.sensor_id,
                        SensorClass.id,
                        ReadingsAdvanticsysClass.temperature,
                        ReadingsAdvanticsysClass.humidity,
                        ReadingsAdvanticsysClass.co2,
                    )
                    .filter(
                        and_(
                            ReadingsAdvanticsysClass.sensor_id == SensorClass.id,
                            ReadingsAdvanticsysClass.timestamp >= dt_from,
                            ReadingsAdvanticsysClass.timestamp <= dt_to,
                        )
                    )
                )

        df = pd.read_sql(query.statement, query.session.bind)

        adv_sensors = df.sensor_id.unique()

        print(adv_sensors)

        return render_template(
                template + ".html",
                adv_sensors=adv_sensors,
                dt_from=dt_from.strftime("%B %d, %Y"),
                dt_to=dt_to.strftime("%B %d, %Y"),
            )


    return render_template(template + ".html")
