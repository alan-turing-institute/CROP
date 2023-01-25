import logging
from TestScenarioV1_1 import testScenario, FILEPATH_WEATHER

# from CalibrationV2 import runCalibration
import pandas as pd
from pathlib import Path
from ges.dataAccess import (
    insert_model_run,
    insert_model_product,
    insert_model_prediction,
)
from ges.config import config

path_conf = config(section="paths")

data_dir = Path(path_conf["data_dir"])
filepath_resultsRH = data_dir / path_conf["filename_resultsrh"]
filepath_resultsT = data_dir / path_conf["filename_resultst"]

cal_conf = config(section="calibration")
MODEL_GES_DATABASE_ID = 3
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


def mock_data():
    T_air = [
        [294.95083093, 294.95083093, 294.04751092, 295.95938605],
        [294.36003495, 294.36003495, 293.40987372, 295.50316643],
        [294.17041032, 294.17041032, 293.23090581, 295.33660461],
    ]

    RH_air = [
        [0.62324361, 0.62324361, 0.62324361, 0.62324361],
        [0.60622243, 0.60622243, 0.56561664, 0.66188203],
        [0.60958018, 0.60958018, 0.57205266, 0.66187175],
    ]
    result = {"T_air": T_air, "RH_air": RH_air}
    return result


def get_forecast_date():
    df_weather = pd.read_csv(
        FILEPATH_WEATHER, header=None, names=["Timestamp", "Temperature", "Humidity"]
    )
    forecast_date = pd.to_datetime(df_weather.tail(1)["Timestamp"].item())
    logging.info("Forecast Date: {0}".format(forecast_date))
    return forecast_date


def assemble_values(product_id, measure, all_results):
    def to_percent(humidity_ratio):
        return humidity_ratio * 100

    def to_celcius(temp_kelvin):
        return temp_kelvin - 273.15

    result_of_type = all_results[measure["result_key"]]
    result_of_measure = []
    for result in result_of_type:
        result_of_measure.append(result[measure["result_index"]])
    result_in_unit = result_of_measure
    if measure["preprocess"] == "to_celcius":
        result_in_unit = list(map(to_celcius, result_of_measure))
    if measure["preprocess"] == "to_percent":
        result_in_unit = list(map(to_percent, result_of_measure))
    prediction_parameters = []
    for prediction_index, result_at_hour in enumerate(result_in_unit):
        prediction_parameters.append((product_id, result_at_hour, prediction_index))
    return prediction_parameters


def main():
    logging.basicConfig(level=logging.INFO)
    forecast_date = get_forecast_date()
    measures = [
        MEASURE_MEAN_TEMPERATURE,
        MEASURE_SCENARIO_TEMPERATURE,
        MEASURE_UPPER_TEMPERATURE,
        MEASURE_LOWER_TEMPERATURE,
        MEASURE_MEAN_HUMIDITY,
        MEASURE_SCENARIO_HUMIDITY,
        MEASURE_LOWER_HUMIDITY,
        MEASURE_UPPER_HUMIDITY,
    ]

    # result = mock_data()
    result = testScenario()
    df_resultsRH = pd.DataFrame(result["RH_air"])
    df_resultsRH.to_csv(filepath_resultsRH, header=False)
    df_resultsT = pd.DataFrame(result["T_air"])
    df_resultsT.to_csv(filepath_resultsT, header=False)

    run_id = insert_model_run(
        sensor_id=SENSOR_RH_16B2_DATABASE_ID,
        model_id=MODEL_GES_DATABASE_ID,
        time_forecast=forecast_date,
    )

    if run_id is not None:
        logging.info("Run inserted, logged as ID: {0}".format(run_id))
        for measure in measures:
            product_id = insert_model_product(
                run_id=run_id, measure_id=measure["measure_database_id"]
            )
            value_parameters = assemble_values(
                product_id=product_id, measure=measure, all_results=result
            )
            logging.info(value_parameters)
            num_rows_inserted = insert_model_prediction(value_parameters)
            logging.info("{0} rows inserted".format(num_rows_inserted))


if __name__ == "__main__":
    main()
