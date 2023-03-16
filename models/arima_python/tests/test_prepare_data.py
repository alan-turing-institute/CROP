import arima.prepare_data as prepare_data
from datetime import datetime
import pandas as pd
import numpy as np

prepare_data.arima_config["farm_cycle_start"] = "16h0m0s"
prepare_data.arima_config["days_interval"] = 30


def test_standardize_timestamp():
    """
    Given a list of input timestamps, test whether the
    function `prepare_data.standardize_timestamp` outputs
    the expected standardized timestamps.
    """
    # list of input timestamps
    input_timestamps = ["2022-12-16 01:00:00"]
    input_timestamps.append("2022-12-16 11:00:00")
    input_timestamps.append("2022-12-16 16:00:00")
    input_timestamps.append("2022-12-17 07:00:00")
    input_timestamps.append("2022-12-17 15:00:00")
    input_timestamps.append("2022-12-16 00:00:00")
    input_timestamps.append("2022-12-15 22:00:00")
    # expected output timestamps when `farm_cycle_start`
    # in config.ini is set to "16h0m0s", as produced by
    # the original R code.
    expect_output_timestamps = ["2022-12-15 16:00:00"]
    expect_output_timestamps.append("2022-12-16 04:00:00")
    expect_output_timestamps.append("2022-12-16 16:00:00")
    expect_output_timestamps.append("2022-12-17 04:00:00")
    expect_output_timestamps.append("2022-12-17 04:00:00")
    expect_output_timestamps.append("2022-12-15 16:00:00")
    expect_output_timestamps.append("2022-12-15 16:00:00")

    for ii in range(len(input_timestamps)):
        # first, parse the strings into datetime objects
        timestamp = datetime.strptime(input_timestamps[ii], "%Y-%m-%d %H:%M:%S")
        output_timestamp = prepare_data.standardize_timestamp(timestamp)
        # convert datetime objects to strings
        output_timestamp = datetime.strftime(output_timestamp, "%Y-%m-%d %H:%M:%S")
        assert output_timestamp == expect_output_timestamps[ii]


def return_temperatures(csv_path: str):
    """
    Given the path of a CSV file, read the "temperature" and
    "expected_temperature" columns and return these as pandas
    Series indexed by timestamp.
    """
    date_parser = lambda x: datetime.strptime(x, "%d/%m/%Y %H:%M:%S")
    df = pd.read_csv(csv_path, parse_dates=["timestamp"], date_parser=date_parser)
    df.set_index("timestamp", inplace=True)
    temperature = df["temperature"]  # with missing values
    temperature_expected = df[
        "expected_temperature"
    ]  # without missing values (replaced manually)
    return temperature, temperature_expected


def test_impute_missing_values():
    """
    Test that the replacement of missing values is performed
    correctly. This function reads CSV files where missing
    values have been replaced manually and checks that the
    function `impute_missing_values` produces the same output.
    """
    # when weekly seasonality is considered
    prepare_data.arima_config["weekly_seasonality"] = True
    csv_path = "tests/data/test_impute_missing_values_weekly_seasonality.csv"
    temperature, temperature_expected = return_temperatures(csv_path)
    temperature_impute_missing = prepare_data.impute_missing_values(temperature)
    assert np.isclose(temperature_expected, temperature_impute_missing).all()
    # when weekly seasonality is not considered
    prepare_data.arima_config["weekly_seasonality"] = False
    csv_path = "tests/data/test_impute_missing_values_no_weekly_seasonality.csv"
    temperature, temperature_expected = return_temperatures(csv_path)
    temperature_impute_missing = prepare_data.impute_missing_values(temperature)
    assert np.isclose(temperature_expected, temperature_impute_missing).all()
