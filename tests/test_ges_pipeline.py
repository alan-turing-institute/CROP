import os
import pytest
import numpy as np
import pandas as pd
import datetime
from models.ges.ges.ges_utils import (
    get_latest_time_hour_value,
    get_scenarios_by_id,
    create_measures_dicts,
)

from models.ges.pipelineV1_1 import (
    get_forecast_date,
    assemble_values,
    run_pipeline,
)

# The following import needs to be 'core' not 'cropcore' in order to
# find the test data, which is not copied to site-packages.
from core.constants import CONST_TESTDATA_GES_FOLDER

from .conftest import check_for_docker

DOCKER_RUNNING = check_for_docker()


def test_get_forecast_date():
    filepath_weather = os.path.join(CONST_TESTDATA_GES_FOLDER, "WeatherV1.csv")
    forecast_date = get_forecast_date(filepath_weather)
    assert isinstance(forecast_date, datetime.datetime)


def mock_data(num_scenarios):
    """
    Emulate the output of TestScenarioV1_1.runModel.

    Parameters
    ----------
    num_scenarios: int, the number of scenarios simulated, including the BAU one

    Returns
    -------
    dict: keys are T_air, RH_air for temp and humidity.  Values are np.arrays
          of dimension (100, num_scenarios+2).  The +2 is because the BAU
          scenario includes upper and lower bounds as well as mean.
    """
    T_air = []
    RH_air = []
    for _ in range(100):
        T_air.append(np.random.normal(293.0, 3.0, num_scenarios + 2))
        RH_air.append(np.random.normal(0.5, 0.1, num_scenarios + 2))
    result = {"T_air": np.array(T_air), "RH_air": np.array(RH_air)}
    return result


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_assemble_values(session):
    scenario_ids = [1, 2, 3, 4, 5]  # scenario_id 1 is BAU
    results = mock_data(num_scenarios=len(scenario_ids))
    measures = create_measures_dicts(
        scenario_ids=scenario_ids, model_name="GES", session=session
    )
    for product_id, measure in enumerate(measures):
        value_parameters = assemble_values(
            product_id=product_id, measure=measure, all_results=results
        )
        assert isinstance(value_parameters, list)
        assert len(value_parameters) == 100
        for i, vp in enumerate(value_parameters):
            assert isinstance(vp, tuple)
            assert len(vp) == 3
            assert vp[0] == product_id
            assert measure["result_key"] in ["T_air", "RH_air"]
            if measure["result_key"] == "T_air":
                assert vp[1] > 0.0 and vp[1] < 40.0  # temp in reasonable range
            elif measure["result_key"] == "RH_air":
                assert vp[1] > 0.0 and vp[1] < 100.0  # RH in reasonable range
            else:
                assert False  # unknown result_key
            assert vp[2] == i


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_pipeline(session):
    """
    This is the big one...
    """
    filepath_weather = os.path.join(CONST_TESTDATA_GES_FOLDER, "WeatherV1.csv")
    filepath_forecast = os.path.join(CONST_TESTDATA_GES_FOLDER, "WeatherForecastV1.csv")
    filepath_ach = os.path.join(CONST_TESTDATA_GES_FOLDER, "ACH_outV1.csv")
    filepath_ias = os.path.join(CONST_TESTDATA_GES_FOLDER, "IAS_outV1.csv")
    rows_written = run_pipeline(
        scenario_ids=[1, 2, 3, 4],
        filepath_ach=filepath_ach,
        filepath_ias=filepath_ias,
        filepath_weather=filepath_weather,
        filepath_forecast=filepath_forecast,
        data_dir=CONST_TESTDATA_GES_FOLDER,
        sensor_id=3,
        model_name="GES",
        session=session,
    )
    assert rows_written > 0
    assert rows_written == 3744
