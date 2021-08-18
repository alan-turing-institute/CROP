"""
A module for the prediction page actions
"""

import logging
import copy
import datetime as dt
import pandas as pd


from app.predictions import blueprint
from flask import request, render_template
from flask_login import login_required

from __app__.crop.structure import (
    ModelClass,
    ModelMeasureClass,
    ModelRunClass,
    ModelValueClass,
    ModelProductClass,
)
from __app__.crop.structure import SQLA as db
from __app__.crop.constants import CONST_TIMESTAMP_FORMAT

def mels_query(dt_from, dt_to):
    """
    Performs a query for mels prediction model.

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
    Returns:
        df: a df with the queried data
    """

    logging.info(
        "Calling zensie_analysis with parameters %s %s"
        % (
            dt_from.strftime(CONST_TIMESTAMP_FORMAT),
            dt_to.strftime(CONST_TIMESTAMP_FORMAT),
        )
    )

    query = db.session.query(
        ModelClass.id
        #ReadingsZensieTRHClass.timestamp,
        #ReadingsZensieTRHClass.sensor_id,
        # SensorClass.name,
        # SensorLocationClass.location_id,
        #LocationClass.zone,
    )#.filter(
     #   and_(
      #      SensorLocationClass.location_id == LocationClass.id,
      #      ReadingsZensieTRHClass.sensor_id == SensorClass.id,
      #      ReadingsZensieTRHClass.sensor_id == SensorLocationClass.sensor_id,
      #      ReadingsZensieTRHClass.timestamp >= dt_from,
       #     ReadingsZensieTRHClass.timestamp <= dt_to,
       # )
    #)

    df = pd.read_sql(query.statement, query.session.bind)

    logging.info("Total number of records found: %d" % (len(df.index)))

    if df.empty:
        logging.debug("WARNING: Query returned empty")

    return df




@blueprint.route('/<template>')
@login_required
def route_template(template, methods=['GET']):
    dt_to = dt.datetime.now()
    dt_from = dt_to - dt.timedelta(days=7)
    df= mels_query(dt_from, dt_to)
    # if request.method == 'GET':
    #     print("!"*100)
    #     #sensors = structure.Sensor.query.all()
    #     #print(sensors)
    #     print("!"*100)

    if template == "melmodel":
        
        print (df)
        return render_template(template + '.html')

    
    else: return render_template(template + '.html')
