from cropcore.model_data_access import (
    get_training_data,
    insert_model_run,
    insert_model_product,
    insert_model_predictions,
)
from arima.clean_data import clean_data
from arima.prepare_data import prepare_data
from arima.arima_pipeline import arima_pipeline
from arima.arima_utils import (
    get_sqlalchemy_session,
    get_model_id,
    get_measure_id,
    get_sensor_id,
)
import logging, coloredlogs
import pandas as pd
import sys
from datetime import datetime


def run_pipeline() -> None:
    # set up logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    field_styles = coloredlogs.DEFAULT_FIELD_STYLES
    coloredlogs.ColoredFormatter(field_styles=field_styles)
    coloredlogs.install(level="INFO")

    # fetch training data from the database
    env_data, energy_data = get_training_data(num_rows=1000)

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

    measure_names = [
        "Mean Temperature (Degree Celcius)",
        "Lower Bound Temperature (Degree Celcius)",
        "Upper Bound Temperature (Degree Celcius)",
    ]
    # loop through every sensor
    for sensor in sensor_names:
        sensor_id = get_sensor_id(sensor_name=sensor)
        temperature = env_data[sensor]["temperature"]
        mean_forecast, conf_int, metrics = arima_pipeline(temperature)
        session.begin()
        try:
            run_id = insert_model_run(sensor_id, model_id, datetime.now())
            for measure_name in measure_names:
                measure_id = get_measure_id(measure_name)
                product_id = insert_model_product(run_id, measure_id)
                print(f"Run ID: {run_id}")
                print(f"Model ID: {model_id}")
                print(f"Product ID: {product_id}")
                print(f"Sensor ID: {sensor_id}")
                print(f"Measure ID: {measure_id}")
                if "Mean" in measure_name:
                    result = process_output(mean_forecast, product_id)
                elif "Lower" in measure_name:
                    result = process_output(conf_int["mean_ci_lower"], product_id)
                elif "Upper" in measure_name:
                    result = process_output(conf_int["mean_ci_upper"], product_id)
                insert_model_predictions(result)
                session.commit()
                session.close()
        except:
            session.rollback()
            session.close()
            raise


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
