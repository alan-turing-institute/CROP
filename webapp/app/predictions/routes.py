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

from sqlalchemy import and_, func

from __app__.crop.structure import (
    ModelClass,
    ModelMeasureClass,
    ModelRunClass,
    ModelValueClass,
    ModelProductClass,
)
from __app__.crop.structure import SQLA as db
from __app__.crop.constants import CONST_TIMESTAMP_FORMAT


def mels_query(dt_from, dt_to, model_id):
    """
    Performs a query for mels prediction model.

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
        model_id: id for a particular model
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

    #subquery to get the last model run from a given model
    sbqr = db.session.query(
        ModelRunClass
    ).filter(
        ModelRunClass.model_id == model_id
    ).all()[-1]

    #quary to get all the results from the model run in the subquery
    query = db.session.query(
        #func.max(ModelProductClass.run_id),
        ModelClass.id,
        ModelClass.model_name,
        ModelRunClass.sensor_id,
        ModelMeasureClass.measure_name,
        ModelValueClass.prediction_value,
        ModelValueClass.prediction_index,
        ModelProductClass.run_id,
    ).filter(
        and_(
            ModelClass.id == model_id,
            ModelRunClass.model_id == ModelClass.id,
            ModelRunClass.id == sbqr.id,
            ModelProductClass.run_id == ModelRunClass.id,
            ModelProductClass.measure_id == ModelMeasureClass.id,
            ModelValueClass.product_id == ModelProductClass.id,

            #ModelRunClass.time_created >= dt_from,
            #ModelRunClass.time_created <= dt_to,
       )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    logging.info("Total number of records found: %d" % (len(df.index)))

    if df.empty:
        logging.debug("WARNING: Query returned empty")

    return df


def json_temp_arima(df_temp):
    """
    Function to return the Json for the temperature related
    charts in the model run

    """
    return (
        df_temp.groupby(["sensor_id", "measure_name"], as_index=True)#"measure_name"
        .apply(lambda x: x[["prediction_value", "prediction_index"]].to_dict("r"))
        .reset_index()
        .rename(columns={0: "Values"})
        .to_json(orient="records")
    )


@blueprint.route('/<template>')
@login_required
def route_template(template, methods=['GET']):
    dt_to = dt.datetime.now()
    dt_from = dt_to - dt.timedelta(days=60)
    df_arima= mels_query(dt_from, dt_to, 1)
    json_arima = json_temp_arima(df_arima)
    print (json_arima)

    #export data in csv for debugging
    #df_arima.to_csv(r'C:\Users\froumpani\OneDrive - The Alan Turing Institute\Desktop\test_data_filter.csv', index = False)

    #print (df_arima)

    # if request.method == 'GET':
    #     print("!"*100)
    #     #sensors = structure.Sensor.query.all()
    #     #print(sensors)
    #     print("!"*100)

    if template == "melmodel":


        return render_template(template + '.html', json_arima_f=json_arima)


    else: return render_template(template + '.html')
