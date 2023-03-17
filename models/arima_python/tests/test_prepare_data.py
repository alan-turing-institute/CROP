import arima.prepare_data as prepare_data
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
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


# import the data processed with `clean_data.clean_data`
env_clean = pd.read_pickle("tests/data/aranet_trh_clean.pkl")
energy_clean = pd.read_pickle("tests/data/utc_energy_clean.pkl")
keys_env_clean = list(env_clean.keys())
# artificially include a missing value in the `temperature`
# column of one of the DataFrames in `env_clean`, to test that it is
# successfully replaced
key_missing_value = keys_env_clean[0]
nrows = env_clean[key_missing_value].shape[0]
env_clean[key_missing_value]["temperature"].iloc[int(nrows / 2)] = None
# switch off `weekly_seasonality` and set the `days_interval`
# parameter to 1 in order to successfully replace the missing observation
prepare_data.arima_config["weekly_seasonality"] = False
prepare_data.arima_config["days_interval"] = 1
# now feed to `prepare_data.prepare_data`
env_prepared, energy_prepared = prepare_data.prepare_data(
    deepcopy(env_clean),
    deepcopy(energy_clean),
)
keys_env_prepared = list(env_prepared.keys())


def test_keys_env_data():
    """
    Test that `env_clean` and `env_prepared` have
    the same keys, which correspond to different sensors.
    """
    assert sorted(keys_env_clean) == sorted(keys_env_prepared)


def test_columns_prepared_data():
    """
    Test that the processed dataframes contain the
    expected columns.
    """
    colnames_env_clean = list(env_clean[keys_env_clean[0]].columns).sort()
    colnames_env_prepared = list(env_prepared[keys_env_prepared[0]].columns).sort()
    colnames_energy_clean = list(energy_clean.columns).sort()
    colnames_energy_prepared = list(energy_prepared.columns).sort()
    assert colnames_env_clean == colnames_env_prepared
    assert colnames_energy_clean == colnames_energy_prepared


def test_timestamps_prepared_data():
    """
    Test the timestamps of the prepared data.
    """
    # check that the timestamp vector is the same for all dataframes
    for ii in range(1, len(keys_env_prepared)):
        timestamp1 = env_prepared[keys_env_prepared[ii - 1]].index
        timestamp2 = env_prepared[keys_env_prepared[ii]].index
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


# def test_missing_values_prepared_data():
#     """
#     Test that artificially inserted missing observations
#     are successfully replaced.
#     """
#     temperature = env_prepared[keyc]
