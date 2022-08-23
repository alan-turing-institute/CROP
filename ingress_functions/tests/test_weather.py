"""
Test ingress_weather.py module
"""
import re
from datetime import datetime, timedelta
import requests
import requests_mock
from __app__.crop.ingress_weather import (
    get_openweathermap_data,
    CONST_OPENWEATHERMAP_URL,
)


def test_get_weather_data():

    dt_from = datetime.utcnow() + timedelta(days=-1)
    dt_to = datetime.utcnow()
    timestamp_from = int(dt_from.timestamp())
    timestamp_to = int(dt_to.timestamp())
    timestamp_avg = int((timestamp_from + timestamp_to) / 2)
    # mock the API response

    mock_response = {
        "hourly": [
            {
                "dt": timestamp_avg,
                "temp": 291.5,
                "pressure": 1016,
                "humidity": 57,
                "wind_speed": 4.44,
                "wind_deg": 259,
                "rain": {"1h": 0.33},
                "weather": [{"icon": "02d"}],
            }
        ]
    }
    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json=mock_response)
        success, error, df = get_openweathermap_data(dt_from, dt_to)
        assert success
        # should have 2 identical rows, from the 2 api calls
        assert len(df) == 2
