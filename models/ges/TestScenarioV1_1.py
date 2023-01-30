import os
import logging
from typing import Dict
import numpy as np
import pandas as pd

# relative imports don't work if we are in same directory
if os.getcwd() == os.path.dirname(os.path.realpath(__file__)):
    from ges.functions_scenarioV1 import (
        derivatives,
        sat_conc,
        FILEPATH_WEATHER,
        FILEPATH_WEATHER_FORECAST,
        FILEPATH_ACH,
        FILEPATH_IAS,
    )
    from ges.config import config
    from ges.ges_utils import get_latest_time_hour_value
else:  # relative imports
    from .ges.functions_scenarioV1 import (
        derivatives,
        sat_conc,
        FILEPATH_WEATHER,
        FILEPATH_WEATHER_FORECAST,
        FILEPATH_ACH,
        FILEPATH_IAS,
    )
    from .ges.config import config
    from .ges.ges_utils import get_latest_time_hour_value

logging.basicConfig(level=logging.INFO)

CAL_CONF = config(section="calibration")

USE_LIVE = False


def getTimeParameters() -> Dict:
    delta_h = int(CAL_CONF["delta_h"])
    ndp = int(CAL_CONF["num_data_points"])
    # The parameter num_data_points is inclusive of the moment of modelling, but for
    # running the scenario evaluation we want to exclude that, so subtract one.
    # TODO This is quite a hacky, ugly solution, figure out something better.
    ndp -= 1
    numDays = int(CAL_CONF["num_weather_days"])
    h1 = 0
    h2 = h1 + ndp * delta_h
    timeParameters: Dict = {
        "h2": h2,
        "h1": h1,
        "ndp": ndp,  # number of data points used for calibration
        "delta_h": delta_h,
        "numDays": numDays,
    }
    logging.info(timeParameters)
    return timeParameters


def setACHParameters(ACH_OUT_PATH: str, ndp: int = 10) -> Dict:
    ACHinp: np.ndarray = np.genfromtxt(ACH_OUT_PATH, delimiter=",")
    ACHcal = (
        ACHinp[1:, -1 * ndp :] * 9 + 1
    )  # selects ACH values corresponding to the last ndp data points
    ACHmean = np.mean(ACHcal, 0)
    ACHuq = np.quantile(ACHcal, 0.95, 0)
    ACHlq = np.quantile(ACHcal, 0.05, 0)
    ACHParameters: Dict = {
        "ACHcal": ACHcal,
        "ACHmean": ACHmean,
        "ACHuq": ACHuq,
        "ACHlq": ACHlq,
    }
    return ACHParameters


def setIASParameters(IAS_OUT_PATH: str, ndp: int = 10) -> Dict:
    IASinp: np.ndarray = np.genfromtxt(IAS_OUT_PATH, delimiter=",")
    IAScal: float = IASinp[1:, -1 * ndp :] * 0.75 + 0.1
    IASmean: float = np.mean(IAScal, 0)
    IASuq: float = np.quantile(IAScal, 0.95, 0)
    IASlq: float = np.quantile(IAScal, 0.05, 0)
    IASParameters: Dict = {
        "IAScal": IASinp[1:, -1 * ndp :] * 0.75 + 0.1,
        "IASmean": IASmean,
        "IASuq": IASuq,
        "IASlq": IASlq,
    }
    return IASParameters


# # Set up parameters for runs: 1) BAU mean, 2) Scenario, 3) BAU UQ, 4) BAU LQ
# # Scenario values N, ndh and lshift will come from sliders on dashboard
def setModel(
    ndp: int = 10, ach_parameters: Dict = {}, ias_parameters: Dict = {}
) -> np.ndarray:

    test: np.ndarray = np.zeros((ndp, 4, 4))

    test[:, 0, 0] = ach_parameters["ACHmean"]
    test[:, 1, 0] = ias_parameters["IASmean"]
    test[:, 2, 0] = 1
    test[:, 3, 0] = 0

    test[:, 0, 1] = ach_parameters["ACHmean"]
    test[:, 1, 1] = ias_parameters["IASmean"]
    test[:, 2, 1] = 1
    test[:, 3, 1] = 0

    test[:, 0, 2] = ach_parameters["ACHuq"]
    test[:, 1, 2] = ias_parameters["IASlq"]
    test[:, 2, 2] = 1
    test[:, 3, 2] = 0

    test[:, 0, 3] = ach_parameters["ACHlq"]
    test[:, 1, 3] = ias_parameters["IASuq"]
    test[:, 2, 3] = 1
    test[:, 3, 3] = 0

    return test


def setScenario(
    ventilation_rate: int = 1,
    num_dehumidifiers: int = 2,
    shift_lighting: int = -3,
    ach_parameters: Dict = {},
    ias_parameters: Dict = {},
    delta_h: int = 3,
) -> np.ndarray:
    number_of_points_in_a_day = int(np.round(24 / delta_h))

    # ScenEval has dimensions of days_by_which_we_extend_the_scenario_into_the_future *
    # number_of_points_in_a_day, 4 for (ACH, IAS, something-about-dehumidifiers,
    # something-about-lighting), 4 for (mean, upper quantile, lower quantile, scenario).
    # # Scenario 1 - vary ACH
    ScenEval: np.ndarray = np.zeros((4 * number_of_points_in_a_day, 4, 4))
    # ScenEval[:,0,0] = ach_parameters['ACHmean'][-1]
    ach_day = ach_parameters["ACHmean"][-number_of_points_in_a_day:]
    ScenEval[:, 0, 0] = np.tile(ach_day, 4)

    ScenEval[:, 0, 1] = ventilation_rate

    # ScenEval[:,0,2] = ach_parameters['ACHuq'][-1]
    achuq_day = ach_parameters["ACHuq"][-number_of_points_in_a_day:]
    ScenEval[:, 0, 2] = np.tile(achuq_day, 4)

    # ScenEval[:,0,3] = ach_parameters['ACHlq'][-1]
    achlq_day = ach_parameters["ACHlq"][-number_of_points_in_a_day:]
    ScenEval[:, 0, 3] = np.tile(achlq_day, 4)

    # ScenEval[:,1,0] = ias_parameters['IASmean'][-1]
    ias_day = ias_parameters["IASmean"][-number_of_points_in_a_day:]
    ScenEval[:, 1, 0] = np.tile(ias_day, 4)

    # ScenEval[:,1,1] = ias_parameters['IASmean'][-1]
    ScenEval[:, 1, 1] = np.tile(ias_day, 4)

    # ScenEval[:,1,2] = ias_parameters['IASlq'][-1]
    iaslq_day = ias_parameters["IASlq"][-number_of_points_in_a_day:]
    ScenEval[:, 1, 2] = np.tile(iaslq_day, 4)

    # ScenEval[:,1,3] = ias_parameters['IASuq'][-1]
    iasuq_day = ias_parameters["IASuq"][-number_of_points_in_a_day:]
    ScenEval[:, 1, 3] = np.tile(iasuq_day, 4)

    # # Scenario 2 - vary number of dehumidifiers
    ScenEval[:, 2, 0] = 1
    ScenEval[:, 2, 1] = int(
        num_dehumidifiers / 2
    )  # ndh input from slider (integer) (/2 as half farm modelled)
    ScenEval[:, 2, 2] = 1
    ScenEval[:, 2, 3] = 1

    # Scenario 3 - shift lighting schedule (+/-hours)
    ScenEval[:, 3, 0] = 0
    ScenEval[:, 3, 1] = shift_lighting
    ScenEval[:, 3, 2] = 0
    ScenEval[:, 3, 3] = 0

    return ScenEval


## Run model, using time varying ACH, IAS corresponding to outputs from calibration for
#  first 10 days, then scenario evaluation values for last 3 days
def runModel(
    time_parameters: Dict,
    filepath_weather=None,
    filepath_weather_forecast=None,
    params: np.ndarray = [],
    LatestTimeHourValue=None,
) -> Dict:
    if not LatestTimeHourValue:
        LatestTimeHourValue = get_latest_time_hour_value()
    results = derivatives(
        time_parameters["h1"],
        time_parameters["h2"],
        time_parameters["numDays"],
        params,
        time_parameters["ndp"],
        filePathWeather=filepath_weather,
        filePathWeatherForecast=filepath_weather_forecast,
        LatestTimeHourValue=LatestTimeHourValue,
    )  # runs GES model over ACH,IAS pairs
    T_air = results[1, :, :]
    Cw_air = results[11, :, :]
    RH_air = Cw_air / sat_conc(T_air)
    results_to_store = {"T_air": T_air, "RH_air": RH_air}
    return results_to_store


# rename from 'testScenario' so that pytest doesn't run as a test (!)
def runScenario():
    # Get calibrated parameters output from calibration model
    # Stored in database? Currently output to csv file
    time_parameters: Dict = getTimeParameters()
    ach_parameters = setACHParameters(
        ACH_OUT_PATH=FILEPATH_ACH, ndp=time_parameters["ndp"]
    )
    ias_parameters: Dict = setIASParameters(
        IAS_OUT_PATH=FILEPATH_IAS, ndp=time_parameters["ndp"]
    )

    ventilation_rate: int = 1
    num_dehumidifiers: int = 2
    shift_lighting: int = -3

    model: np.ndarray = setModel(
        time_parameters["ndp"],
        ach_parameters=ach_parameters,
        ias_parameters=ias_parameters,
    )

    scenario: np.ndarray = setScenario(
        ventilation_rate=ventilation_rate,
        num_dehumidifiers=num_dehumidifiers,
        shift_lighting=shift_lighting,
        ach_parameters=ach_parameters,
        ias_parameters=ias_parameters,
        delta_h=time_parameters["delta_h"],
    )

    params: np.ndarray = np.concatenate(
        (model, scenario)
    )  # put scenario on the end of the calibrated parameters
    LatestTimeHourValue = get_latest_time_hour_value()
    results = runModel(
        time_parameters=time_parameters,
        filepath_weather=None if USE_LIVE else FILEPATH_WEATHER,
        filepath_weather_forecast=None if USE_LIVE else FILEPATH_WEATHER_FORECAST,
        params=params,
        LatestTimeHourValue=LatestTimeHourValue,
    )

    return results


if __name__ == "__main__":
    runScenario()
