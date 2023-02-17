import os
import logging
from typing import Dict
import numpy as np
import pandas as pd

from cropcore.structure import ScenarioType

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
    from ges.ges_utils import (
        get_latest_time_hour_value,
        get_scenarios_by_id,
        get_scenarios,
    )
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
    from .ges.ges_utils import (
        get_latest_time_hour_value,
        get_scenarios_by_id,
        get_scenarios,
    )

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


# # Set up parameters for runs: 1) BAU mean, 2) BAU UQ, 3) BAU LQ   4...N) alternative scenarios
# # Scenario values N, ndh and lshift will come from sliders on dashboard
def setModel(
    ndp: int = 10,
    num_test_scenarios: int = 1,
    ach_parameters: Dict = {},
    ias_parameters: Dict = {},
) -> np.ndarray:
    """
    Create an output array containing values of
    ACH, IAS, num_dehumidifiers, lighting shift,
    for each "Measure", for each timepoint in previous 10 days.

    Parameters
    ----------
    ndp:int, number of data points, i.e. number of days x 24/delta_h
    num_test_scenarios:int, number of scenarios, NOT INCLUDING the
                       Business-As-Usual scenario
    ach_parameters: dict, read from CSV file output by calibration
    ias_parameters: dict, read from CSV file output by calibration.

    Returns
    -------
    test: np.array of dimension (ndp, 4, num_test_scenarios+3)
          Note that the +3 is because the BAU scenario has three values,
          mean, upper, and lower, while the test scenarios have just
          a mean value each.
    """
    # set the size of the output array
    test: np.ndarray = np.zeros((ndp, 4, 3 + num_test_scenarios))
    # BusinessAsUsual
    test[:, 0, 0] = ach_parameters["ACHmean"]
    test[:, 1, 0] = ias_parameters["IASmean"]
    test[:, 2, 0] = 1
    test[:, 3, 0] = 0
    # BAU UQ
    test[:, 0, 1] = ach_parameters["ACHuq"]
    test[:, 1, 1] = ias_parameters["IASlq"]
    test[:, 2, 1] = 1
    test[:, 3, 1] = 0
    # BAU LQ
    test[:, 0, 2] = ach_parameters["ACHlq"]
    test[:, 1, 2] = ias_parameters["IASuq"]
    test[:, 2, 2] = 1
    test[:, 3, 2] = 0
    # scenarios
    for i in range(num_test_scenarios):
        test[:, 0, i + 3] = ach_parameters["ACHmean"]
        test[:, 1, i + 3] = ias_parameters["IASmean"]
        test[:, 2, i + 3] = 1
        test[:, 3, i + 3] = 0

    return test


def setScenarios(
    scenarios_df: pd.DataFrame,
    ach_parameters: Dict = {},
    ias_parameters: Dict = {},
    delta_h: int = 3,
) -> np.ndarray:
    """
    Setup the arrays for projecting various scenarios into the future.

    Parameters
    ----------
    """

    number_of_points_in_a_day = int(np.round(24 / delta_h))

    # if the BAU scenario is in our scenarios_df, exclude it - we only need "Test" scenarios
    scenarios_df = scenarios_df[scenarios_df.scenario_type != ScenarioType.BAU]
    scenarios_df.reset_index(inplace=True)

    # ScenEval has dimensions of:
    #    ndays_into_the_future*number_of_points_in_a_day,
    # x  4 for (ACH, IAS, num_dehumidifiers, lighting_shift),
    # x  3+num_scenarios for (mean, upper quantile, lower quantile, scenario_0, scenario_1,...)

    ScenEval: np.ndarray = np.zeros(
        (4 * number_of_points_in_a_day, 4, 3 + len(scenarios_df))
    )

    # Business-As-Usual
    ach_day = ach_parameters["ACHmean"][-number_of_points_in_a_day:]
    ScenEval[:, 0, 0] = np.tile(ach_day, 4)
    ias_day = ias_parameters["IASmean"][-number_of_points_in_a_day:]
    ScenEval[:, 1, 0] = np.tile(ias_day, 4)
    ScenEval[:, 2, 0] = 1
    ScenEval[:, 3, 0] = 0

    # BAU upper quartile
    achuq_day = ach_parameters["ACHuq"][-number_of_points_in_a_day:]
    ScenEval[:, 0, 1] = np.tile(achuq_day, 4)
    iaslq_day = ias_parameters["IASlq"][-number_of_points_in_a_day:]
    ScenEval[:, 1, 1] = np.tile(iaslq_day, 4)
    ScenEval[:, 2, 1] = 1
    ScenEval[:, 3, 1] = 0

    # BAU lower quartile
    achlq_day = ach_parameters["ACHlq"][-number_of_points_in_a_day:]
    ScenEval[:, 0, 2] = np.tile(achlq_day, 4)
    iasuq_day = ias_parameters["IASuq"][-number_of_points_in_a_day:]
    ScenEval[:, 1, 2] = np.tile(iasuq_day, 4)
    ScenEval[:, 2, 2] = 1
    ScenEval[:, 3, 2] = 0

    # test scenarios
    for i, row in scenarios_df.iterrows():
        ScenEval[:, 0, 3 + i] = row.ventilation_rate
        ScenEval[:, 1, 3 + i] = np.tile(ias_day, 4)
        ScenEval[:, 2, 3 + i] = int(
            row.num_dehumidifiers
        )  # ndh input from slider (integer) corresponding to
           # number of dehumidifiers in the half-farm we are simulating
        ScenEval[:, 3, 3 + i] = row.lighting_shift
        pass

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
    """
    Run ges.derivatives over the arrays that were produced by setModel and
    setScenario.   Will return two arrays of results, one for temp and one
    for humidity, which are then put into a dictionary.

    Parameters
    ----------
    time_parameters: dict, as obtained by getTimeParameters()
    filepath_weather: str, location of WeatherV1.csv (if None use default)
    filepath_weather_forecast: str, location of WeatherForecastV1.csv
    params: np.array of dimension (timepoints, 4, 3+num_test_scenarios)
    LatestTimeHourValue: float, last hour from the weather csv file.
    """
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
def runScenarios(
    scenario_ids=[],
    filepath_ach=None,
    filepath_ias=None,
    filepath_weather=None,
    filepath_forecast=None,
    session=None,
):
    """
    Run both the model for the previous 8 days and the various test scenarios
    for the upcoming few days.

    Parameters
    ==========
    scenario_idss:list of ints, ids of scenarios in the DB to run.
                     Default is empty list, in which case, will run all scenarios
                     for the GES model.
    filepath_ach, filepath_ias, filepath_weather, filepath_forecast: str, directories containing
                     calibration output.  Only needed if they will be non-standard
                     (e.g. for testing).
    session: sqlalchemy.session, only needed if using a non-default DB (e.g. for testing).

    Returns
    =======
    results: dict, keyed by "T_air", "RH_air", with values np.arrays
             of dim (n_timepoints, 3+n_test_scenario)
    """
    # if scenario_indices is empty, run all scenarios for this model
    if (scenario_ids is None) or (len(scenario_ids) == 0):
        scenarios_df = get_scenarios(session=session)
    else:
        scenarios_df = get_scenarios_by_id(scenario_ids, session=session)
    num_scenarios = len(scenarios_df)
    # how many scenarios, discounting the BusinessAsUsual one?
    num_test_scenarios = len(
        scenarios_df[scenarios_df.scenario_type != ScenarioType.BAU]
    )
    if not filepath_ach:
        filepath_ach = FILEPATH_ACH
    if not filepath_ias:
        filepath_ias = FILEPATH_IAS
    if not filepath_weather:
        filepath_weather = FILEPATH_WEATHER
    if not filepath_forecast:
        filepath_forecast = FILEPATH_WEATHER_FORECAST
    # Get calibrated parameters output from calibration model
    # Stored in database? Currently output to csv file
    time_parameters: Dict = getTimeParameters()
    ach_parameters = setACHParameters(
        ACH_OUT_PATH=filepath_ach, ndp=time_parameters["ndp"]
    )
    ias_parameters: Dict = setIASParameters(
        IAS_OUT_PATH=filepath_ias, ndp=time_parameters["ndp"]
    )

    model: np.ndarray = setModel(
        time_parameters["ndp"],
        num_test_scenarios=num_test_scenarios,
        ach_parameters=ach_parameters,
        ias_parameters=ias_parameters,
    )

    scenario: np.ndarray = setScenarios(
        scenarios_df=scenarios_df,
        ach_parameters=ach_parameters,
        ias_parameters=ias_parameters,
        delta_h=time_parameters["delta_h"],
    )

    params: np.ndarray = np.concatenate(
        (model, scenario)
    )  # put scenario on the end of the calibrated parameters
    LatestTimeHourValue = get_latest_time_hour_value(os.path.dirname(filepath_weather))
    results = runModel(
        time_parameters=time_parameters,
        filepath_weather=None if USE_LIVE else filepath_weather,
        filepath_weather_forecast=None if USE_LIVE else filepath_forecast,
        params=params,
        LatestTimeHourValue=LatestTimeHourValue,
    )
    return results


if __name__ == "__main__":
    runScenarios()
