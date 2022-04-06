"""
Module for data upload logs.
"""

from datetime import datetime, timedelta
from flask import render_template, request
from flask_login import login_required
from sqlalchemy import and_, desc

from app.logs import blueprint
from utilities.utils import query_result_to_array

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import DataUploadLogClass, TypeClass
from __app__.crop.constants import CONST_MAX_RECORDS


@blueprint.route("/<template>")
@login_required
def route_template(template):
    """
    Main method to render templates.
    """

    if request.method == "GET":

        dt_to = (
            datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            + timedelta(days=1)
            + timedelta(milliseconds=-1)
        )
        dt_from = (dt_to + timedelta(-30)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        query_result = (
            db.session.query(
                DataUploadLogClass.time_created,
                TypeClass.sensor_type,
                DataUploadLogClass.filename,
                DataUploadLogClass.status,
                DataUploadLogClass.log,
            )
            .filter(
                and_(
                    DataUploadLogClass.time_created <= dt_to,
                    DataUploadLogClass.time_created >= dt_from,
                    DataUploadLogClass.type_id == TypeClass.id,
                )
            )
            .order_by(desc(DataUploadLogClass.time_created))
            .limit(CONST_MAX_RECORDS)
        )

        logs = db.session.execute(query_result).fetchall()

        results_arr = query_result_to_array(logs, date_iso=False)

        return render_template(template + ".html", logs=results_arr)

    return None
