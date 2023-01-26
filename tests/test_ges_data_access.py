import pytest
from datetime import datetime
from models.ges.ges.dataAccess import (
    get_days_weather,
    get_days_weather_forecast,
    get_days_humidity_temperature,
    get_days_humidity,
    get_datapoint_humidity,
    get_data_point,
)


def test_get_days_weather():
    result = get_days_weather()
    assert len(result) == 5
    # check right format
    for r in result:
        assert len(r) == 3
        assert isinstance(r[0], datetime)
        assert isinstance(r[1], float)
        assert isinstance(r[2], float)


def test_get_days_weather_forecast():
    result = get_days_weather_forecast()
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


def test_get_days_humidity_temperature():
    result = get_days_humidity_temperature()
    assert len(result) == 5
    # check right format
    for r in result:
        assert len(r) == 3
        assert isinstance(r[0], datetime)
        assert isinstance(r[1], float)
        assert isinstance(r[2], float)


def test_get_days_humidity():
    result = get_days_humidity()
    assert len(result) == 5
    # check right format
    for r in result:
        assert len(r) == 2
        assert isinstance(r[0], datetime)
        assert isinstance(r[1], float)


def test_get_datapoint_humidity():
    result = get_datapoint_humidity()
    assert len(result) == 1
    assert len(result[0]) == 2
    assert isinstance(result[0][0], datetime)
    assert isinstance(result[0][1], float)


def test_get_datapoint():
    result = get_data_point()
    # should be just one number?
    assert isinstance(result, float)
