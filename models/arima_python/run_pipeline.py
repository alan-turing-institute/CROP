from cropcore.model_data_access import get_training_data
from arima.clean_data import clean_data
from arima.prepare_data import prepare_data
from arima.arima_pipeline import arima_pipeline
from arima.arima_utils import get_sqlalchemy_session, get_model_id
import logging, coloredlogs
import pandas as pd
import sys


def run_pipeline() -> None:
    # set up logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    field_styles = coloredlogs.DEFAULT_FIELD_STYLES
    coloredlogs.ColoredFormatter(field_styles=field_styles)
    coloredlogs.install(level="INFO")

    # fetch training data from the database
    env_data, energy_data = get_training_data()

    # clean the training data
    env_data, energy_data = clean_data(env_data, energy_data)

    # prepare the clean data for the ARIMA model
    env_data, energy_data = prepare_data(env_data, energy_data)

    # run the ARIMA pipeline for every temperature sensor
    # note that in this implementation, energy data is not used at all
    sensor_names = list(env_data.keys())

    session = get_sqlalchemy_session()
    model_id = get_model_id()

    def process_output(time_series: pd.Series, product_id):
        prediction_parameters = []
        for prediction_index, result_at_hour in enumerate(time_series):
            prediction_parameters.append((product_id, result_at_hour, prediction_index))
        return prediction_parameters

    # loop through every sensor
    for sensor in sensor_names:
        # sensor_id = get_sensor_id(name=sensor)
        temperature = env_data[sensor]["temperature"]
        mean_forecast, conf_int, metrics = arima_pipeline(temperature)
        # run_id = insert_model_run(sensor_id, model_id, dt.now())
        # mean_measure_id = get_measure_id("Mean Temperature (Degree Celcius)")
        # lower_measure_id = get_measure_id("Lower Bound Temperature (Degree Celcius)")
        # upper_measure_id = get_measure_id("Upper Bound Temperature (Degree Celcius)")
        # mean_product_id = insert_model_product(run_id, measure_id)
        # mean_forecast = process_output(mean_forecast, mean_product_id)
        # insert_model_predictions(mean_forecast)


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
