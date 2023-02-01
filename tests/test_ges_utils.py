import pytest
from datetime import datetime
import pandas as pd

# The following import needs to be 'core' not 'cropcore' in order to
# find the test data, which is not copied to site-packages.
from core.constants import CONST_TESTDATA_GES_FOLDER

from models.ges.ges.ges_utils import (
    get_ges_model_id,
    get_bau_scenario_id,
    get_scenarios,
    get_scenarios_by_id,
    get_measures,
    get_weather_data_from_file,
    get_latest_time_hour_value,
    create_measures_dicts,
)
from .conftest import check_for_docker

DOCKER_RUNNING = check_for_docker()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_model_id(session):
    result = get_ges_model_id(model_name="GES", session=session)
    assert result
    assert result == 2


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_bau_scenario_id(session):
    result = get_bau_scenario_id(model_name="GES", session=session)
    assert result
    assert result == 1


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_scenarios(session):
    result = get_scenarios(model_name="GES", session=session)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 76  # 5x3x5 'Test' plus BAU.


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_scenarios_by_id(session):
    result = get_scenarios_by_id(scenario_ids=[5, 7, 9, 11], session=session)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 4  # will automagically add scenario 1.


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_measures_all_scenarios(session):
    result = get_measures(model_name="GES", session=session)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 156  # 2x5x3x5 'Test' plus six previous ones.


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_measures_interactive_scenarios(session):
    """
    For all scenarios apart from the default one, there should be exactly two measures
    (Mean Humidity and Mean Temperature)
    """
    # choose a couple of integers between 3 and 377 (no need to do 374 queries!)
    scenario_ids = [4, 10, 20, 30]
    result = get_measures(scenario_ids=scenario_ids, model_name="GES", session=session)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 8  # 2 per scenario


def test_get_weather_data_from_file():
    """
    Test reading the weather csv file for GES
    """
    df = get_weather_data_from_file(CONST_TESTDATA_GES_FOLDER)
    assert isinstance(df, pd.DataFrame)


def test_get_latest_time_hour_value():
    """
    Test getting the hour of the last row in weather csv
    """
    latest_hour = get_latest_time_hour_value(CONST_TESTDATA_GES_FOLDER)
    assert latest_hour == 13.0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_create_measures_dicts(session):
    """
    Test creation of the list of dicts describing "measures"
    (e.g. Mean Temperature for scenario_id=2)
    """
    result = create_measures_dicts(
        scenario_ids=[3, 4, 5], model_name="GES", session=session
    )
    assert isinstance(result, list)
    assert len(result) == 12  # 2x (3(BAU)+3x2)
