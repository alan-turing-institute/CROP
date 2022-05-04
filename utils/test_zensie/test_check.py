import os
import requests
import json
import pandas as pd

from datetime import datetime, timedelta


CONST_CROP_30MHZ_APIKEY = os.environ["CROP_30MHZ_APIKEY"].strip()
CONST_CROP_30MHZ_TEST_T_RH_CHECKID = os.environ["CROP_30MHZ_TEST_T_RH_CHECKID"].strip()


def main():
    """
    Main test routine
    """

    test_check()


def get_sensor_data(api_key, check_id, dt_from, dt_to):
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
        "Content-Type": "application/json",
        "Authorization": api_key,
    }

    url_path = "https://api.30mhz.com/api/stats/check"
    params = "statisticType=averages&intervalSize=5m"

    dt_from_iso = dt_from.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    dt_to_iso = dt_to.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    url = "{}/{}/from/{}/until/{}?{}".format(
        url_path, check_id, dt_from_iso, dt_to_iso, params
    )

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
        data_df.rename(columns={"index": "Timestamp"}, inplace=True)

        for col_name in data_df.columns:

            if ".temperature" in col_name:
                data_df.rename(columns={col_name: "Temperature"}, inplace=True)

            elif ".humidity" in col_name:
                data_df.rename(columns={col_name: "Humidity"}, inplace=True)

    return success, error, data_df


def test_check():
    """ """

    check_id = CONST_CROP_30MHZ_TEST_T_RH_CHECKID

    dt_from = datetime.now() + timedelta(days=-1)
    dt_to = datetime.now()

    success, error, _ = get_sensor_data(
        CONST_CROP_30MHZ_APIKEY, check_id, dt_from, dt_to
    )

    assert success, error


if __name__ == "__main__":

    main()
