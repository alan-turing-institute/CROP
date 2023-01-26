import pytest
from datetime import datetime
from models.ges.ges.dataAccess import (
    get_days_weather,
    get_days_weather_forecast,
    get_days_humidity_temperature,
    get_days_humidity,
    get_datapoint_humidity,
    get_datapoint,
    insert_model_run,
    insert_model_product,
    insert_model_prediction,
)
from .conftest import check_for_docker

DOCKER_RUNNING = check_for_docker()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_days_weather(session):
    result = get_days_weather(session=session)
    assert len(result) == 5
    # check right format
    for r in result:
        assert len(r) == 3
        assert isinstance(r[0], datetime)
        assert isinstance(r[1], float)
        assert isinstance(r[2], float)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_days_weather_forecast(session):
    result = get_days_weather_forecast(session=session)
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


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_days_humidity_temperature(session):
    result = get_days_humidity_temperature(sensor_id=2, session=session)
    assert len(result) == 5
    # check right format
    for r in result:
        assert len(r) == 3
        assert isinstance(r[0], datetime)
        assert isinstance(r[1], float)
        assert isinstance(r[2], float)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_days_humidity(session):
    result = get_days_humidity(sensor_id=2, session=session)
    assert len(result) == 5
    # check right format
    for r in result:
        assert len(r) == 2
        assert isinstance(r[0], datetime)
        assert isinstance(r[1], float)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_datapoint_humidity(session):
    result = get_datapoint_humidity(sensor_id=2, session=session)
    assert len(result) == 1
    assert len(result[0]) == 2
    assert isinstance(result[0][0], datetime)
    assert isinstance(result[0][1], float)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_datapoint(session):
    result = get_datapoint(sensor_id=2, session=session)
    # should be just one number?
    assert isinstance(result, float)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model_run(session):
    time_now = datetime.now()
    run_id = insert_model_run(3, 2, session=session)
