"""
Test ingress_weather.py module
"""
from datetime import datetime, timedelta

from __app__.crop.constants import (
    CONST_CROP_30MHZ_APIKEY,
    CONST_CROP_30MHZ_TEST_T_RH_CHECKID,
    CONST_ZENSIE_WEATHER_SENSOR_TYPE,
)

from __app__.crop.ingress_weather import get_api_weather_data

# def test_get_sensor_data():

#     check_id = CONST_CROP_30MHZ_TEST_T_RH_CHECKID

#     dt_from = datetime.now() + timedelta(days=-1)
#     dt_to = datetime.now()

#     success, error, _ = get_api_sensor_data(CONST_CROP_30MHZ_APIKEY, check_id, dt_from, dt_to)

#     assert success is True, error
