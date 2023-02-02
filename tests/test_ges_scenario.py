import os
import pytest
from datetime import datetime
import numpy as np
import pandas as pd

from models.ges.ges.ges_utils import get_latest_time_hour_value, get_scenarios_by_id

from models.ges.TestScenarioV1_1 import (
    getTimeParameters,
    setACHParameters,
    setIASParameters,
    setModel,
    setScenarios,
    runModel,
    runScenarios,
)

# The following import needs to be 'core' not 'cropcore' in order to
# find the test data, which is not copied to site-packages.
from core.constants import CONST_TESTDATA_GES_FOLDER
from cropcore.structure import ModelScenarioClass
from .conftest import check_for_docker

DOCKER_RUNNING = check_for_docker()


def test_get_time_parameters():
    result = getTimeParameters()
    assert isinstance(result, dict)
    assert "delta_h" in result.keys()


def test_set_ach_parameters():
    filepath_ach = os.path.join(CONST_TESTDATA_GES_FOLDER, "ACH_outV1.csv")
    time_parameters = getTimeParameters()
    result = setACHParameters(filepath_ach, time_parameters["ndp"])
    assert result
    assert isinstance(result, dict)
    assert "ACHmean" in result.keys()


def test_set_ias_parameters():
    filepath_ias = os.path.join(CONST_TESTDATA_GES_FOLDER, "IAS_outV1.csv")
    time_parameters = getTimeParameters()
    result = setIASParameters(filepath_ias, time_parameters["ndp"])
    assert result
    assert isinstance(result, dict)
    assert "IASmean" in result.keys()


def test_set_model_one_test_scenario():
    time_parameters = getTimeParameters()
    filepath_ach = os.path.join(CONST_TESTDATA_GES_FOLDER, "ACH_outV1.csv")
    filepath_ias = os.path.join(CONST_TESTDATA_GES_FOLDER, "IAS_outV1.csv")
    ach_params = setACHParameters(filepath_ach, time_parameters["ndp"])
    ias_params = setIASParameters(filepath_ias, time_parameters["ndp"])
    model = setModel(
        time_parameters["ndp"], ach_parameters=ach_params, ias_parameters=ias_params
    )
    assert isinstance(model, np.ndarray)
    assert model.shape == (80, 4, 4)


def test_set_model_five_test_scenarios():
    time_parameters = getTimeParameters()
    filepath_ach = os.path.join(CONST_TESTDATA_GES_FOLDER, "ACH_outV1.csv")
    filepath_ias = os.path.join(CONST_TESTDATA_GES_FOLDER, "IAS_outV1.csv")
    ach_params = setACHParameters(filepath_ach, time_parameters["ndp"])
    ias_params = setIASParameters(filepath_ias, time_parameters["ndp"])
    model = setModel(
        time_parameters["ndp"],
        num_test_scenarios=5,
        ach_parameters=ach_params,
        ias_parameters=ias_params,
    )
    assert isinstance(model, np.ndarray)
    assert model.shape == (80, 4, 8)


def test_set_scenario_default():
    time_parameters = getTimeParameters()
    filepath_ach = os.path.join(CONST_TESTDATA_GES_FOLDER, "ACH_outV1.csv")
    filepath_ias = os.path.join(CONST_TESTDATA_GES_FOLDER, "IAS_outV1.csv")
    ach_params = setACHParameters(filepath_ach, time_parameters["ndp"])
    ias_params = setIASParameters(filepath_ias, time_parameters["ndp"])
    scenarios_df = pd.DataFrame(
        {
            "ventilation_rate": [1],
            "num_dehumidifiers": [2],
            "lighting_shift": [-3],
            "scenario_type": "Test",
        }
    )
    scenario = setScenarios(
        scenarios_df=scenarios_df,
        ach_parameters=ach_params,
        ias_parameters=ias_params,
        delta_h=time_parameters["delta_h"],
    )
    assert isinstance(scenario, np.ndarray)
    assert len(scenario) == 32
    assert scenario.shape == (32, 4, 4)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_set_scenario_from_db(session):
    time_parameters = getTimeParameters()
    filepath_ach = os.path.join(CONST_TESTDATA_GES_FOLDER, "ACH_outV1.csv")
    filepath_ias = os.path.join(CONST_TESTDATA_GES_FOLDER, "IAS_outV1.csv")
    ach_params = setACHParameters(filepath_ach, time_parameters["ndp"])
    ias_params = setIASParameters(filepath_ias, time_parameters["ndp"])
    scenarios_df = get_scenarios_by_id([5], session)
    scenario = setScenarios(
        scenarios_df=scenarios_df,
        ach_parameters=ach_params,
        ias_parameters=ias_params,
        delta_h=time_parameters["delta_h"],
    )
    assert isinstance(scenario, np.ndarray)
    assert len(scenario) == 32
    assert scenario.shape == (32, 4, 4)


def test_run_model_default():
    time_parameters = getTimeParameters()
    filepath_weather = os.path.join(CONST_TESTDATA_GES_FOLDER, "WeatherV1.csv")
    filepath_forecast = os.path.join(CONST_TESTDATA_GES_FOLDER, "WeatherForecastV1.csv")
    filepath_ach = os.path.join(CONST_TESTDATA_GES_FOLDER, "ACH_outV1.csv")
    filepath_ias = os.path.join(CONST_TESTDATA_GES_FOLDER, "IAS_outV1.csv")
    ach_params = setACHParameters(filepath_ach, time_parameters["ndp"])
    ias_params = setIASParameters(filepath_ias, time_parameters["ndp"])
    model = setModel(
        time_parameters["ndp"], ach_parameters=ach_params, ias_parameters=ias_params
    )
    scenarios_df = pd.DataFrame(
        {
            "ventilation_rate": [1],
            "num_dehumidifiers": [2],
            "lighting_shift": [-3],
            "scenario_type": "Test",
        }
    )
    scenario = setScenarios(
        scenarios_df=scenarios_df,
        ach_parameters=ach_params,
        ias_parameters=ias_params,
        delta_h=time_parameters["delta_h"],
    )
    params: np.ndarray = np.concatenate((model, scenario))
    latest_time_hour_value = get_latest_time_hour_value(CONST_TESTDATA_GES_FOLDER)
    results = runModel(
        time_parameters=time_parameters,
        filepath_weather=filepath_weather,
        filepath_weather_forecast=filepath_forecast,
        params=params,
        LatestTimeHourValue=latest_time_hour_value,
    )
    assert isinstance(results, dict)
    assert "RH_air" in results.keys()
    assert "T_air" in results.keys()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_run_scenarios(session):
    filepath_weather = os.path.join(CONST_TESTDATA_GES_FOLDER, "WeatherV1.csv")
    filepath_forecast = os.path.join(CONST_TESTDATA_GES_FOLDER, "WeatherForecastV1.csv")
    filepath_ach = os.path.join(CONST_TESTDATA_GES_FOLDER, "ACH_outV1.csv")
    filepath_ias = os.path.join(CONST_TESTDATA_GES_FOLDER, "IAS_outV1.csv")
    results = runScenarios(
        scenario_ids=[3, 4, 5],
        filepath_ach=filepath_ach,
        filepath_ias=filepath_ias,
        filepath_weather=filepath_weather,
        filepath_forecast=filepath_forecast,
        session=session,
    )
    assert isinstance(results, dict)
    assert "RH_air" in results.keys()
    assert "T_air" in results.keys()
    # 2nd dim of results array should be 6 (3 BAU + 3 test scenarios)
    assert results["T_air"].shape == (312, 6)
