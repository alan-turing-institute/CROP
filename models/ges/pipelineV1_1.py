import os
import logging
import pandas as pd
from pathlib import Path

# relative or non-relative imports, depending on where we run from :-/
if os.getcwd() == os.path.dirname(os.path.realpath(__file__)):
    from TestScenarioV1_1 import runScenarios, FILEPATH_WEATHER
    from ges.dataAccess import (
        insert_model_run,
        insert_model_product,
        insert_model_predictions,
    )
    from ges.config import config
    from ges.ges_utils import (
        get_ges_model_id,
        get_scenarios,
        create_measures_dicts,
        get_sqlalchemy_session,
    )
else:
    from .TestScenarioV1_1 import runScenarios, FILEPATH_WEATHER
    from .ges.dataAccess import (
        insert_model_run,
        insert_model_product,
        insert_model_predictions,
    )
    from .ges.config import config
    from .ges.ges_utils import (
        get_ges_model_id,
        get_scenarios,
        create_measures_dicts,
        get_sqlalchemy_session,
    )

path_conf = config(section="paths")
DATA_DIR = Path(path_conf["data_dir"])


cal_conf = config(section="calibration")
MODEL_GES_NAME = cal_conf["model_name"]
SENSOR_RH_16B2_DATABASE_ID = int(cal_conf["sensor_id"])

MEASURE_MEAN_TEMPERATURE = {
    "measure_database_id": 1,
    "result_index": 0,
    "preprocess": "to_celcius",
    "result_key": "T_air",
}
MEASURE_SCENARIO_TEMPERATURE = {
    "measure_database_id": 9,
    "result_index": 1,
    "preprocess": "to_celcius",
    "result_key": "T_air",
}
MEASURE_UPPER_TEMPERATURE = {
    "measure_database_id": 2,
    "result_index": 3,
    "preprocess": "to_celcius",
    "result_key": "T_air",
}
MEASURE_LOWER_TEMPERATURE = {
    "measure_database_id": 3,
    "result_index": 2,
    "preprocess": "to_celcius",
    "result_key": "T_air",
}

MEASURE_MEAN_HUMIDITY = {
    "measure_database_id": 10,
    "result_index": 0,
    "preprocess": "to_percent",
    "result_key": "RH_air",
}
MEASURE_SCENARIO_HUMIDITY = {
    "measure_database_id": 11,
    "result_index": 1,
    "preprocess": "to_percent",
    "result_key": "RH_air",
}
MEASURE_LOWER_HUMIDITY = {
    "measure_database_id": 12,
    "result_index": 2,
    "preprocess": "to_percent",
    "result_key": "RH_air",
}
MEASURE_UPPER_HUMIDITY = {
    "measure_database_id": 13,
    "result_index": 3,
    "preprocess": "to_percent",
    "result_key": "RH_air",
}


def get_forecast_date(filepath_weather=None):
    if not filepath_weather:
        filepath_weather = FILEPATH_WEATHER
    df_weather = pd.read_csv(
        filepath_weather, header=None, names=["Timestamp", "Temperature", "Humidity"]
    )
    forecast_date = pd.to_datetime(df_weather.tail(1)["Timestamp"].item())
    logging.info("Forecast Date: {0}".format(forecast_date))
    return forecast_date


def assemble_values(product_id, measure, all_results):
    """
    Process the output of TestScenarioV1_1.runModel() to put it into a
    form ready to be inserted to the DB.

    Parameters
    ----------
    product_id: int, index of the (run x measure) product in the DB.
    measure: dict, as produced by ges_utils.create_measures_dicts
    all_results: dict, keyed by T_air, RH_air, values are np.array of
                 dimension (num_timepoints, num_scenarios+2) (where the +2
                 is because the Business-As-Usual scenario has upper and
                 lower bounds as well as the mean).

    Returns
    -------
    prediction_parameters: list of tuples, of length num_timepoints, with
                         each tuple containing (product_id, result, pred_index)
                         where result is the value of that measure at that time.
    """

    def to_percent(humidity_ratio):
        return humidity_ratio * 100

    def to_celcius(temp_kelvin):
        return temp_kelvin - 273.15

    result_of_type = all_results[measure["result_key"]]
    result_of_measure = []
    for result in result_of_type:
        this_result = result[measure["result_index"]]
        result_of_measure.append(this_result)
    result_in_unit = result_of_measure
    if measure["preprocess"] == "to_celcius":
        result_in_unit = list(map(to_celcius, result_of_measure))
    if measure["preprocess"] == "to_percent":
        result_in_unit = list(map(to_percent, result_of_measure))
    prediction_parameters = []
    for prediction_index, result_at_hour in enumerate(result_in_unit):
        prediction_parameters.append((product_id, result_at_hour, prediction_index))
    return prediction_parameters


def run_pipeline(
    scenario_ids=None,
    filepath_ach=None,
    filepath_ias=None,
    filepath_weather=None,
    filepath_forecast=None,
    data_dir=DATA_DIR,
    sensor_id=SENSOR_RH_16B2_DATABASE_ID,
    model_name=MODEL_GES_NAME,
    session=None,
):
    """
    Run all the test scenarios and upload results to DB
    """
    if not session:
        session = get_sqlalchemy_session()
    logging.basicConfig(level=logging.INFO)
    forecast_date = get_forecast_date(filepath_weather)
    model_id = get_ges_model_id(model_name, session=session)
    measures = create_measures_dicts(
        scenario_ids=scenario_ids, model_name=model_name, session=session
    )
    result = runScenarios(
        scenario_ids=scenario_ids,
        filepath_ach=filepath_ach,
        filepath_ias=filepath_ias,
        filepath_weather=filepath_weather,
        filepath_forecast=filepath_forecast,
        session=session,
    )
    filepath_resultsRH = os.path.join(data_dir, path_conf["filename_resultsrh"])
    filepath_resultsT = os.path.join(data_dir, path_conf["filename_resultst"])
    df_resultsRH = pd.DataFrame(result["RH_air"])
    df_resultsRH.to_csv(filepath_resultsRH, header=False)
    df_resultsT = pd.DataFrame(result["T_air"])
    df_resultsT.to_csv(filepath_resultsT, header=False)

    run_id = insert_model_run(
        sensor_id=sensor_id,
        model_id=model_id,
        time_forecast=forecast_date,
        session=session,
    )
    num_rows_inserted = 0
    if run_id is not None:
        logging.info("Run inserted, logged as ID: {0}".format(run_id))
        for measure in measures:
            product_id = insert_model_product(
                run_id=run_id,
                measure_id=measure["measure_database_id"],
                session=session,
            )
            # Don't try to add values unless we successfully added a run x measure "product".
            if not product_id:
                continue
            value_parameters = assemble_values(
                product_id=product_id, measure=measure, all_results=result
            )
            logging.info(value_parameters)
            num_rows_inserted += insert_model_predictions(
                value_parameters, session=session
            )
            logging.info("{0} rows inserted".format(num_rows_inserted))
    return num_rows_inserted


def main():
    # run with all default parameters
    run_pipeline()


if __name__ == "__main__":
    main()
