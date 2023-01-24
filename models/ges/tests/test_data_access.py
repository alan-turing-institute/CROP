import pytest
from datetime import datetime
from ges.dataAccess import (
    getDaysWeather,
    getDaysWeatherForecast,
    getDaysHumidityTemp,
    getDaysHumidity,
    getDataPointHumidity,
    getDataPoint,
)


def test_get_days_weather():
    result = getDaysWeather()
    assert len(result) == 5
    # check right format
    for r in result:
        assert len(r) == 3
        assert isinstance(r[0], datetime)
        assert isinstance(r[1], float)
        assert isinstance(r[2], float)


def test_get_days_weather_forecast():
    result = getDaysWeatherForecast()
    assert len(result) > 0
    # check right format
    for r in result:
        assert len(r) == 3
        assert isinstance(r[0], datetime)
        assert isinstance(r[1], float)
        assert isinstance(r[2], float)
    # check no duplicates
    dts = [r[0] for r in result]
    assert len(dts) == len(set(dts))
    assert dts == sorted(dts)


def test_get_day_humidity_temperature():
    result = getDaysHumidityTemp()
    assert len(result) == 5
    # check right format
    for r in result:
        assert len(r) == 3
        assert isinstance(r[0], datetime)
        assert isinstance(r[1], float)
        assert isinstance(r[2], float)


def test_get_day_humidity():
    result = getDaysHumidity()
    assert len(result) == 5
    # check right format
    for r in result:
        assert len(r) == 2
        assert isinstance(r[0], datetime)
        assert isinstance(r[1], float)


def test_get_datapoint_humidity():
    result = getDataPointHumidity()
    assert len(result) == 1
    assert len(result[0]) == 2
    assert isinstance(result[0][0], datetime)
    assert isinstance(result[0][1], float)


def test_get_datapoint():
    result = getDataPoint()
    # should be just one number?
    assert isinstance(r, float)
