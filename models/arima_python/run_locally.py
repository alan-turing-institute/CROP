def main() -> None:
    from arima.data_access import get_training_data
    from arima.clean_data import clean_data
    from arima.prepare_data import prepare_data
    from arima.arima_pipeline import arima_pipeline
    from collections import defaultdict
    import pickle
    import logging, coloredlogs
    import sys

    # set up logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    field_styles = coloredlogs.DEFAULT_FIELD_STYLES
    field_styles["levelname"][
        "color"
    ] = "white"  # change the default levelname color from black to white
    coloredlogs.ColoredFormatter(field_styles=field_styles)
    coloredlogs.install(level="INFO")

    # fetch training data from the database
    env_data, energy_data = get_training_data(num_rows=30000)

    # save the raw training data to disk
    with open("dump/env_raw.pkl", "wb") as handle:
        pickle.dump(env_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open("dump/energy_raw.pkl", "wb") as handle:
        pickle.dump(energy_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # clean the training data
    env_data, energy_data = clean_data(env_data, energy_data)

    # save the clean data to disk
    with open("dump/env_clean.pkl", "wb") as handle:
        pickle.dump(env_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open("dump/energy_clean.pkl", "wb") as handle:
        pickle.dump(energy_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # prepare the clean data for the ARIMA model
    env_data, energy_data = prepare_data(env_data, energy_data)

    # save the prepared data to disk
    with open("dump/env_prepared.pkl", "wb") as handle:
        pickle.dump(env_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open("dump/energy_prepared.pkl", "wb") as handle:
        pickle.dump(energy_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # run the ARIMA pipeline for every temperature sensor
    sensor_names = list(env_data.keys())
    forecast_results = defaultdict(dict)

    # loop through every sensor
    for sensor in sensor_names:
        temperature = env_data[sensor]["temperature"]
        mean_forecast, conf_int, metrics = arima_pipeline(temperature)
        forecast_results[sensor]["mean_forecast"] = mean_forecast
        forecast_results[sensor]["conf_int"] = conf_int
        forecast_results[sensor]["metrics"] = metrics

    # save the forecast results to disk
    with open("dump/temperature_forecast.pkl", "wb") as handle:
        pickle.dump(forecast_results, handle, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    main()
