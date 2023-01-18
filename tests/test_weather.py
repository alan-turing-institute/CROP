"""
Test ingress_weather.py module
"""
import os
import re
import json

from datetime import datetime, timedelta
import requests
import requests_mock

from core.constants import CONST_TESTDATA_WEATHER_FOLDER
from core.ingress_weather import (
    get_openweathermap_data as get_openweathermap_history,
)

from core.ingress_weather_forecast import (
    get_openweathermap_data as get_openweathermap_forecast,
)


MOCK_OPENWEATHERMAP_HISTORY = json.load(
    open(os.path.join(CONST_TESTDATA_WEATHER_FOLDER, "weatherHistory.json"))
)

MOCK_OPENWEATHERMAP_FORECAST = json.load(
    open(os.path.join(CONST_TESTDATA_WEATHER_FOLDER, "weatherForecast.json"))
)


def test_get_weather_history_data():

    dt_from = datetime.utcnow() + timedelta(days=-1)
    dt_to = datetime.utcnow()
    timestamp_from = int(dt_from.timestamp())
    timestamp_to = int(dt_to.timestamp())
    timestamp_avg = int((timestamp_from + timestamp_to) / 2)
    # mock the API response
    mock_response = MOCK_OPENWEATHERMAP_HISTORY
    # replace the timestamp in the mock response with timestamp_avg
    mock_response["hourly"][0]["dt"] = timestamp_avg
    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json=mock_response)
        success, error, df = get_openweathermap_history(dt_from, dt_to)
        assert success
        # should have 2 identical rows, from the 2 api calls
        assert len(df) == 2


def test_get_weather_forecast_data():

    dt_now = datetime.utcnow()
    dt_to = datetime.utcnow() + timedelta(days=1)
    timestamp_now = int(dt_now.timestamp())
    timestamp_to = int(dt_to.timestamp())
    mock_response = MOCK_OPENWEATHERMAP_FORECAST
    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json=mock_response)
        success, error, df = get_openweathermap_forecast(dt_to)
        assert success
