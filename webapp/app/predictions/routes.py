"""
A module for the prediction page actions
"""

import logging
import copy
import datetime as dt
import pandas as pd
from pandas.core.frame import DataFrame


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
    ReadingsZensieTRHClass,
    SensorLocationClass,
    LocationClass,
    SensorClass
)

from __app__.crop.structure import SQLA as db
from __app__.crop.constants import CONST_TIMESTAMP_FORMAT


def zensie_query(dt_from, dt_to):
    """
    Performs a query for zensie sensors.

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
        ReadingsZensieTRHClass.timestamp,
        ReadingsZensieTRHClass.sensor_id,
        # SensorClass.name,
        ReadingsZensieTRHClass.temperature,
        ReadingsZensieTRHClass.humidity,
        # SensorLocationClass.location_id,
        LocationClass.zone,
    ).filter(
        and_(
            SensorLocationClass.location_id == LocationClass.id,
            ReadingsZensieTRHClass.sensor_id == SensorClass.id,
            ReadingsZensieTRHClass.sensor_id == SensorLocationClass.sensor_id,
            ReadingsZensieTRHClass.timestamp >= dt_from,
            ReadingsZensieTRHClass.timestamp <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    logging.info("Total number of records found: %d" % (len(df.index)))

    if df.empty:
        logging.debug("WARNING: Query returned empty")

    return df


def arima_query(dt_from, dt_to, model_id, sensor_id):
    """
    Performs a query for the arima prediction model.

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
        model_id: id for a particular model
    Returns:
        df: a df with the queried data
    """

    logging.info(
        "Calling arima model with parameters %s %s"
        % (
            dt_from.strftime(CONST_TIMESTAMP_FORMAT),
            dt_to.strftime(CONST_TIMESTAMP_FORMAT),
        )
    )

    # subquery to get the last model run from a given model

    sbqr = db.session.query(
        ModelRunClass
    ).filter(
        ModelRunClass.model_id == model_id,
        ModelRunClass.sensor_id == sensor_id,
    ).all()[-1]
    


    # query to get all the results from the model run in the subquery
    query = db.session.query(
        # func.max(ModelProductClass.run_id),
        ModelClass.id,
        ModelClass.model_name,
        ModelRunClass.sensor_id,
        ModelMeasureClass.measure_name,
        ModelValueClass.prediction_value,
        ModelValueClass.prediction_index,
        ModelProductClass.run_id,
        ModelRunClass.time_created,
        ModelRunClass.time_forecast
    ).filter(
        and_(
            ModelClass.id == model_id,
            ModelRunClass.model_id == ModelClass.id,
            ModelRunClass.id == sbqr.id,
            ModelProductClass.run_id == ModelRunClass.id,
            ModelProductClass.measure_id == ModelMeasureClass.id,
            ModelValueClass.product_id == ModelProductClass.id,
            ModelRunClass.sensor_id == sensor_id,

            #ModelRunClass.time_created >= dt_from,
            #ModelRunClass.time_created <= dt_to,
        )
    )
    #print(query.statement.compile(dialect=db.session.bind.dialect))

    df = pd.read_sql(query.statement, query.session.bind)

    logging.info("Total number of records found: %d" % (len(df.index)))

    if df.empty:
        logging.debug("WARNING: Query returned empty")

    return df

def resample(df):
    """
    Resamples (date per hour) to a dataframe.

    Arguments:
        temp_df: dataframe with temperature assign to bins
        bins: temperature or humidity bins as a list
    Returns:
        temp_df: the df with grouped bins
    """


    # Reseting index
    df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)
    df_grp_hr = df.groupby('sensor_id').resample('H', on='timestamp').agg({'temperature':'mean', 'humidity':'mean'}).reset_index()

    return df_grp_hr



def json_temp_arima(df_arima):
    """
    Function to return the Json for the temperature related
    charts in the model run

    """

    #create timestamps from prediction index and convert date to string
    time_ = []
    timestamp_ = []
    for i in range (len(df_arima)):
        pred_id = int(df_arima["prediction_index"][i])
        pred_time = df_arima["time_forecast"][i] + dt.timedelta(hours=pred_id)
        format_time = pred_time.strftime("%d-%m-%Y %H:%M:%S")
        time_.append(format_time)
        timestamp_.append(pred_time)

    df_arima["time"]= time_
    df_arima["timestamp"]= timestamp_

    # df_temp =  df_arima.groupby(["sensor_id", "measure_name"], as_index=True).apply(lambda x: x[["prediction_value", "prediction_index", "run_id","time", "timestamp"]].to_dict("r")).reset_index()
    # print ("ajja", df_temp)
    # df_temp2 =  DataFrame({'Values' : df_temp.groupby( "sensor_id" ).apply(lambda x: x[["measure_name"]].to_dict("r"))}).reset_index()
    # print ("asdf", df_temp2["Values"][0])


    #print ("timetype:", type(df_temp["time"][0]))
    return (
        df_arima.groupby(["sensor_id" , "measure_name","run_id"], as_index=True)  # "measure_name"
        .apply(lambda x: x[["prediction_value", "prediction_index", "run_id","time", "timestamp"]].to_dict("r"))
        .reset_index()
        .rename(columns={0: "Values"})
        .to_json(orient="records")
    )


def json_temp_zensie (dt_from_daily, dt_to):
    df = zensie_query(dt_from_daily, dt_to)  
    
    if not df.empty:
        #resample zensie data per hour
        df_grp_hr = resample(df)
        
        time_ = []
        for i in range (len(df_grp_hr)):
            time = df_grp_hr["timestamp"][i]
            format_time = time.strftime("%d-%m-%Y %H:%M:%S")
            time_.append(format_time)

        df_grp_hr["time"]= time_

        #.groupby('sensor_id').resample('H', on='timestamp').agg({'temperature':'mean', 'humidity':'mean'})
        return (
            df_grp_hr.groupby(["sensor_id"], as_index=True)  # "measure_name"
            .apply(lambda x: x[["temperature", "humidity", "time", "timestamp"]].to_dict("r"))
            .reset_index()
            .rename(columns={0: "Values"})
            .to_json(orient="records")
        )
    else:
        return ({})


@blueprint.route('/<template>')
@login_required
def route_template(template, methods=['GET']):
    #arima data
    dt_to = dt.datetime(2021, 12, 4, 00, 00) #dt.datetime.now()
    dt_from = dt_to - dt.timedelta(days=3)

    df_arima_18 = arima_query(dt_from, dt_to, 1, 18)
    df_arima_23 = arima_query(dt_from, dt_to, 1, 23)
    df_arima_27 = arima_query(dt_from, dt_to, 1, 27)
    
    df_arima_ = df_arima_23.append(df_arima_18, ignore_index = True)
    df_arima = df_arima_.append(df_arima_27, ignore_index = True)
    
    json_arima = json_temp_arima(df_arima)


    #zensie data
    unique_time_forecast = df_arima['time_forecast'].unique()
    date_time = pd.to_datetime(unique_time_forecast[0])
    dt_to_z = date_time + dt.timedelta(days=+3) #datetime(2021, 6, 16)
    dt_from_z = dt_to_z + dt.timedelta(days=-5)
    json_zensie = json_temp_zensie(dt_from_z , dt_to_z)

    unique_time_forecast_18 = df_arima_18['time_forecast'].unique()
    date_time_18 = pd.to_datetime(unique_time_forecast_18[0])
    dt_to_z_18 = date_time_18 + dt.timedelta(days=+3) #datetime(2021, 6, 16)
    dt_from_z_18 = dt_to_z_18 + dt.timedelta(days=-5)
    json_zensie_18 = json_temp_zensie(dt_from_z_18 , dt_to_z_18)

    unique_time_forecast_23 = df_arima_23['time_forecast'].unique()
    date_time_23 = pd.to_datetime(unique_time_forecast_23[0])
    dt_to_z_23 = date_time_23 + dt.timedelta(days=+3) #datetime(2021, 6, 16)
    dt_from_z_23 = dt_to_z_23 + dt.timedelta(days=-5)
    json_zensie_23 = json_temp_zensie(dt_from_z_23 , dt_to_z_23)

    unique_time_forecast_27 = df_arima_27['time_forecast'].unique()
    date_time_27 = pd.to_datetime(unique_time_forecast_27[0])
    dt_to_z_27 = date_time_27 + dt.timedelta(days=+3) #datetime(2021, 6, 16)
    dt_from_z_27 = dt_to_z_27 + dt.timedelta(days=-5)
    json_zensie_27 = json_temp_zensie(dt_from_z_27 , dt_to_z_27)


    # export data in csv for debugging
    #df_arima.to_csv(r'C:\Users\froumpani\OneDrive - The Alan Turing Institute\Desktop\test_data_filter.csv', index = False)


    # if request.method == 'GET':
    #     print("!"*100)
    #     #sensors = structure.Sensor.query.all()
    #     #print(sensors)
    #     print("!"*100)

    if template == "arima":

        return render_template(template + '.html',
        json_arima_f=json_arima,
        json_zensie_f=json_zensie,
        json_zensie_18_f=json_zensie_18,
        json_zensie_23_f=json_zensie_23,
        json_zensie_27_f=json_zensie_27,


        )

    else:
        return render_template(template + '.html')
