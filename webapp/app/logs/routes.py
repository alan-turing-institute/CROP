from datetime import datetime, timedelta
from flask import render_template, request
from flask_login import login_required
from sqlalchemy import and_, desc

from app.logs import blueprint

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import DataUploadLogClass, TypeClass

@blueprint.route('/<template>')
@login_required
def route_template(template, methods=['GET']):

    if request.method == 'GET':
        
        dt_to = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1) + timedelta(milliseconds=-1)
        dt_from = (dt_to + timedelta(-30)).replace(hour=0, minute=0, second=0, microsecond=0)

        query = db.session.query(
            DataUploadLogClass.time_created,
            TypeClass.sensor_type,
            DataUploadLogClass.filename,
            DataUploadLogClass.status,
            DataUploadLogClass.log,
        ).filter(
            and_(
                DataUploadLogClass.time_created <= dt_to,
                DataUploadLogClass.time_created >= dt_from,
                DataUploadLogClass.type_id == TypeClass.id,
            )
        ).order_by(desc(DataUploadLogClass.time_created))

        logs = db.session.execute(query).fetchall()

        dict_entry, results_arr = {}, []
        for rowproxy in logs:
            # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
            for column, value in rowproxy.items():
                if isinstance(value, datetime):
                    dict_entry = {**dict_entry, **{column: value.replace(microsecond=0)}}
                else:
                    dict_entry = {**dict_entry, **{column: value}}

            results_arr.append(dict_entry)

        return render_template(template + '.html', logs=results_arr)
