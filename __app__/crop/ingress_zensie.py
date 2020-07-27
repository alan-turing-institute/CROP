"""
Python module to import data using 30 MHz
"""

import os
import requests
import json
import pandas as pd


from __app__.crop.constants import (
    CONST_CROP_30MHZ_APIKEY,
)


CONST_CHECK_URL_PATH = 'https://api.30mhz.com/api/stats/check'
CONST_CHECK_PARAMS = 'statisticType=averages&intervalSize=5m'


def get_api_sensor_data(api_key, check_id, dt_from, dt_to):
    """
    Makes a request to download sensor data for a specified period of time.

    Arguments:
        api_key: api key for authetication
        check_id: sensor identifier 
        dt_from: date range from
        dt_to: date range to
    Return:
        success: whether data request was succesful
        error: error message
        data_df: sensor data as pandas dataframe
    """

    success = True
    error = ""
    data_df = None

    headers = {
        'Content-Type': 'application/json',
        'Authorization': api_key,
    }

    dt_from_iso = dt_from.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    dt_to_iso = dt_to.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    
    url = '{}/{}/from/{}/until/{}?{}'.format(CONST_CHECK_URL_PATH, check_id, dt_from_iso, dt_to_iso, CONST_CHECK_PARAMS)

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data_df = pd.read_json(response.content).T

        if data_df.empty:
            error = "Request [%s]: no data" % (url)
            success = False

    else:
        error = "Request's [%s] status code: %d" % (url, response.status_code)
        success = False
    
    if success:
        data_df.reset_index(inplace=True, drop=False)
        data_df.rename(columns={'index': 'Timestamp'}, inplace=True)

        for col_name in data_df.columns:

            if ".temperature" in col_name:
                data_df.rename(columns={col_name: 'Temperature'}, inplace=True)

            elif ".humidity" in col_name:
                data_df.rename(columns={col_name: 'Humidity'}, inplace=True)

    return success, error, data_df

