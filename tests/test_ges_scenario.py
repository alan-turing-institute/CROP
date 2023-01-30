import os
import pytest
from datetime import datetime
import numpy as np
import pandas as pd

from models.ges.ges.ges_utils import get_latest_time_hour_value

from models.ges.TestScenarioV1_1 import (
    getTimeParameters,
    setACHParameters,
    setIASParameters,
    setModel,
    setScenario,
    runModel,
    runScenario,
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


def test_set_model():
    time_parameters = getTimeParameters()
    filepath_ach = os.path.join(CONST_TESTDATA_GES_FOLDER, "ACH_outV1.csv")
    filepath_ias = os.path.join(CONST_TESTDATA_GES_FOLDER, "IAS_outV1.csv")
    ach_params = setACHParameters(filepath_ach, time_parameters["ndp"])
    ias_params = setIASParameters(filepath_ias, time_parameters["ndp"])
    model = setModel(
        time_parameters["ndp"], ach_parameters=ach_params, ias_parameters=ias_params
    )
    assert isinstance(model, np.ndarray)
    assert model.shape == (40, 4, 4)


def test_set_scenario_default():
    time_parameters = getTimeParameters()
    filepath_ach = os.path.join(CONST_TESTDATA_GES_FOLDER, "ACH_outV1.csv")
    filepath_ias = os.path.join(CONST_TESTDATA_GES_FOLDER, "IAS_outV1.csv")
    ach_params = setACHParameters(filepath_ach, time_parameters["ndp"])
    ias_params = setIASParameters(filepath_ias, time_parameters["ndp"])
    scenario = setScenario(
        ventilation_rate=1,
        num_dehumidifiers=2,
        shift_lighting=3,
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
    query = session.query(
        ModelScenarioClass.ventilation_rate,
        ModelScenarioClass.num_dehumidifiers,
        ModelScenarioClass.lighting_shift,
    )
    scenario_params = session.execute(query).fetchall()[-1]
    scenario = setScenario(
        ventilation_rate=scenario_params[0],
        num_dehumidifiers=scenario_params[1],
        shift_lighting=scenario_params[2],
        ach_parameters=ach_params,
        ias_parameters=ias_params,
        delta_h=time_parameters["delta_h"],
    )
    assert isinstance(scenario, np.ndarray)
    assert len(scenario) == 32
    assert scenario.shape == (32, 4, 4)


def test_run_scenario_default():
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
    scenario = setScenario(
        ventilation_rate=1,
        num_dehumidifiers=2,
        shift_lighting=3,
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
