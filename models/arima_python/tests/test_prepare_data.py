import arima.prepare_data as prepare_data
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pickle
from copy import deepcopy

prepare_data.arima_config["farm_cycle_start"] = "16h0m0s"


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


def return_temperatures(csv_path: str) -> tuple[pd.Series, pd.Series]:
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
    # make sure the `dyas_interval` parameter is set to 30 days,
    # that's how the test CSV files have been set up.
    prepare_data.arima_config["days_interval"] = 30
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


def get_prepared_data(
    env_data: dict, energy_data: pd.DataFrame
) -> tuple[dict, pd.DataFrame]:
    """
    Given environment and energy data pre-processed with
    `clean_data.clean_data`, artificially insert a missing
    value in the `temperature` column of the first DataFrame
    in `env_data`, and call the function `prepare_data.prepare_data`.
    The missing observation is introduced to test that it is
    successfully replaced with a typically-observed value.
    """
    keys = list(env_data.keys())
    # artificially include a missing value in the `temperature`
    # column of the first dataframe in `env_data`
    nrows = env_data[keys[0]].shape[0]
    env_data[keys[0]]["temperature"].iloc[int(nrows / 2)] = np.NaN
    # switch off `weekly_seasonality` and set the `days_interval`
    # parameter to 1 in order to successfully replace missing observations
    prepare_data.arima_config["weekly_seasonality"] = False
    prepare_data.arima_config["days_interval"] = 1
    # now feed to `prepare_data.prepare_data`
    env_data, energy_data = prepare_data.prepare_data(
        env_data,
        energy_data,
    )
    return env_data, energy_data


# import the data processed with `clean_data.clean_data`
env_clean = pd.read_pickle("tests/data/aranet_trh_clean.pkl")
energy_clean = pd.read_pickle("tests/data/utc_energy_clean.pkl")
# get the prepared data
env_prepared, energy_prepared = get_prepared_data(
    deepcopy(env_clean),
    deepcopy(energy_clean),
)


def test_timestamps_prepared_data():
    """
    Test the timestamps of the prepared data.
    """
    # check that the timestamp vector is the same for all dataframes
    keys = list(env_prepared.keys())
    for ii in range(1, len(keys)):
        timestamp1 = env_prepared[keys[ii - 1]].index
        timestamp2 = env_prepared[keys[ii]].index
        assert timestamp2.equals(timestamp1)
    timestamp1 = energy_prepared.index
    assert timestamp2.equals(timestamp1)
    # check that the timestamp vector is monotonically increasing
    assert timestamp2.is_monotonic_increasing
    # check that the timedelta is unique
    timestamp2 = timestamp2.to_series()
    time_delta = timestamp2.diff()[1:]
    time_delta = pd.unique(time_delta)
    assert len(time_delta) == 1
    # check that the last timestamp has time `farm_cycle_start`
    # or (`farm_cycle_start`- 12 hours)
    farm_cycle_start = prepare_data.arima_config["farm_cycle_start"]
    farm_cycle_start = datetime.strptime(farm_cycle_start, "%Hh%Mm%Ss")
    assert (
        timestamp2[-1].time() == farm_cycle_start.time()
        or timestamp2[-1].time() == (farm_cycle_start - timedelta(hours=12)).time()
    )
