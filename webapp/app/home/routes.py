"""
Analysis dashboards module.
"""

import pandas as pd
import json
from datetime import timedelta, date

from flask_login import login_required
from flask import render_template, request, jsonify
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


TEMP_BINS = [0, 17, 21, 24, 30]


def resample(df, bins, dt_from, dt_to):
    """
    Resamples (adds missing date/temperature bin combinations) to a dataframe.
    
    Arguments:
        df: dataframe with temperature assign to bins
        bins: temperature bins as a list
        dt_from: date range from
        dt_to: date range to
    Returns:
        bins_list: a list of temperature bins
        df_list: a list of df corresponding to temperature bins
    """
    
    bins_list = []
    for i in range(len(bins)-1):
        bins_list.append("(%d, %d]" % (bins[i], bins[i+1]))
    
    date_min = min(df['date'].min(), dt_from)
    date_max = max(df['date'].max(), dt_to)
    
    for n in range(int ((date_max - date_min).days) + 1):
        day = date_min + timedelta(n)
        
        for temp_range in bins_list:
            if (len(df[(df['date'] == day) & (df['temp_bin'] == temp_range)].index) == 0):
                
                df2 = pd.DataFrame({
                        "date": [day], 
                        "temp_bin": [temp_range],
                        "temp_cnt": [0]
                }) 
                
                df = df.append(df2) 
                
    df = df.sort_values(by=['date', 'temp_bin'], ascending=True)
    
    df.reset_index(inplace=True, drop=True)

    df_list = []

    for bin_range in bins_list:

        df_bin = df[df["temp_bin"] == bin_range]

        del df_bin["temp_bin"]

        df_bin.reset_index(inplace=True, drop=True)
        
        df_list.append(df_bin)

    return bins_list, df_list

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

    if template == "temperature":
        adv_sensors_temp = {}

        dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

        # advanticsys
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
        
        if not df.empty:
           
            # unique sensors
            adv_sensors = df.sensor_id.unique()
            adv_sensors_modbus_ids = df.id.unique()

            # extracting date from datetime
            df['date'] = pd.to_datetime(df['timestamp'].dt.date)

            # Reseting index
            df.sort_values(by=['timestamp'], ascending=True).reset_index(inplace=True)
            
            # grouping data by date-hour and sensor id
            adv_grp = df.groupby(by=[
                df.timestamp.map(lambda x : "%04d-%02d-%02d-%02d" % (x.year, x.month, x.day, x.hour)), 
                'sensor_id', 'date'])

            # estimating hourly temperature mean values
            adv_grp_temp = adv_grp['temperature'].mean().reset_index()

            # binning temperature values
            adv_grp_temp['temp_bin'] = pd.cut(adv_grp_temp['temperature'], TEMP_BINS)

            # converting bins to str
            adv_grp_temp['temp_bin'] = adv_grp_temp['temp_bin'].astype(str)

            # get bin counts for each sensor-day combination
            adv_grp_date = adv_grp_temp.groupby(by=['sensor_id', 'date', 'temp_bin'])
            adv_cnt = adv_grp_date['temperature'].count().reset_index()
            adv_cnt.rename(columns={'temperature': 'temp_cnt'}, inplace=True)

            json_data = []
            for adv_sensor_id in adv_sensors:

                adv_cnt_sensor = adv_cnt[adv_cnt['sensor_id'] == adv_sensor_id]

                del adv_cnt_sensor['sensor_id']

                # Adding missing date/temp_bin combos
                bins_list, df_list = resample(adv_cnt_sensor, TEMP_BINS, dt_from, dt_to)
                
                bins_json = []

                for i in range(len(bins_list)):
                    bin_range = bins_list[i]
                    temp_bin_df = df_list[i]
                    temp_bin_df['date'] = pd.to_datetime(temp_bin_df['date'], format = '%Y-%m-%d').dt.strftime('%Y-%m-%d')
                
                    bins_json.append('["' + bin_range + '",' + temp_bin_df.to_json(orient='records') + ']')

                json_data.append('[' + ','.join(bins_json) + ']')

            adv_sensors_temp['data'] = '[' + ','.join(json_data) + ']'

        else:
            adv_sensors_modbus_ids = []
            
        return render_template(
                template + ".html",
                num_adv_sensors=len(adv_sensors_modbus_ids),
                adv_sensors=adv_sensors_modbus_ids,
                adv_sensors_temp=adv_sensors_temp,
                dt_from=dt_from.strftime("%B %d, %Y"),
                dt_to=dt_to.strftime("%B %d, %Y"),
            )

    return render_template(template + ".html")
