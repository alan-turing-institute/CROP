# Updates TestScenario_V1 by repeating last 8 values of calibrated ACH/IAS 4 times instead of fixing at final value

from typing import Dict
from functions_scenarioV1 import (
    derivatives,
    sat_conc,
    FILEPATH_WEATHER,
    FILEPATH_ACH,
    FILEPATH_IAS,
)
import numpy as np
import pandas as pd

# import os
USE_LIVE = False

# Import Weather Data
header_list = ["DateTime", "T_e", "RH_e"]
Weather = pd.read_csv(FILEPATH_WEATHER, delimiter=",", names=header_list)

# Latest timestamp for weather and monitored data - hour (for lights)
Weather_hour = pd.DataFrame(Weather, columns=["DateTime", "T_e", "RH_e"]).set_index(
    "DateTime"
)
LatestTime = Weather_hour[-1:]
LatestTimeHourValue = pd.DatetimeIndex(LatestTime.index).hour.astype(float)[0]


def setTimeParameters(
    h2: int = 240, numDays: int = 10, hours_per_point: int = 3
) -> Dict:
    # Start hour h2 is for test only - in live version will be current time
    # h2 = 240
    h1: int = h2 - 240  # select previous 10 days
    ndp: int = int(
        (h2 - h1) / hours_per_point
    )  # number of data points used for calibration
    timeParameters: Dict = {
        "h2": h2,
        "h1": h1,  # select previous 10 days
        "ndp": ndp,  # number of data points used for calibration
        "numDays": numDays,
    }
    print(timeParameters)
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
    hours_per_point: int = 3,
) -> np.ndarray:
    number_of_points_in_a_day = int(np.round(24 / hours_per_point))

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
    params: np.ndarray = [],
    LatestTimeHourValue=LatestTimeHourValue,
) -> Dict:

    results = derivatives(
        time_parameters["h1"],
        time_parameters["h2"],
        time_parameters["numDays"],
        params,
        time_parameters["ndp"],
        filePathWeather=filepath_weather,
        LatestTimeHourValue=LatestTimeHourValue,
    )  # runs GES model over ACH,IAS pairs
    T_air = results[1, :, :]
    Cw_air = results[11, :, :]
    RH_air = Cw_air / sat_conc(T_air)
    results_to_store = {"T_air": T_air, "RH_air": RH_air}
    return results_to_store


def testScenario():
    # Get calibrated parameters output from calibration model
    # Stored in database? Currently output to csv file
    h2: int = 240
    numDays: int = 10
    hours_per_point = 3  # TODO This needs to match the one used in GESCalibrationV1

    time_parameters: Dict = setTimeParameters(
        h2=h2, numDays=numDays, hours_per_point=hours_per_point
    )
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
        hours_per_point=hours_per_point,
    )

    params: np.ndarray = np.concatenate(
        (model, scenario)
    )  # put scenario on the end of the calibrated parameters

    results = runModel(
        time_parameters=time_parameters,
        filepath_weather=None if USE_LIVE else FILEPATH_WEATHER,
        params=params,
        LatestTimeHourValue=LatestTimeHourValue,
    )

    return results


if __name__ == "__main__":
    testScenario()
