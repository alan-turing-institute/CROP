import pandas as pd
import arima.clean_data as clean_data

# import the sample raw (un-processed) data
env_raw = pd.read_pickle(
    "tests/data/aranet_trh_raw.pkl"
)  # temperature/rel humidity (TRH) data
energy_raw = pd.read_pickle("tests/data/utc_energy_raw.pkl")  # energy data

# import the processed data - this is the baseline we compare against
env_clean = pd.read_pickle("tests/data/aranet_trh_processed.pkl")
energy_clean = pd.read_pickle("tests/data/utc_energy_processed.pkl")
keys_clean = list(env_clean.keys())

# column names TRH data should contain
colnames_env = list(env_clean[keys_clean[0]].columns)

# column names energy data should contain
colnames_energy = list(energy_clean.columns)

# Set the TRH sensors and processing parameters of the cleanData module to those
# of the baseline dataset loaded above.
# This is done here because these are parameters that can be specified by the user
# via the config file, so here we are simply overwriting them.
clean_data.sensors_list = keys_clean
clean_data.processing_params["mins_from_the_hour"] = 15
clean_data.processing_params["time_delta"] = "1h0m0s"
clean_data.processing_params["window"] = 3

# now call the function to process the raw data
env_data, energy_data = clean_data.clean_data(env_raw, energy_raw)
keys = list(env_data.keys())


def test_format_clean_data():
    """
    Test that the format of the processed data is
    the expected one.
    """
    # chect that variable types are correct
    assert isinstance(env_data, dict)
    for sensor in keys:
        assert isinstance(env_data[sensor], pd.DataFrame)
    assert isinstance(energy_data, pd.DataFrame)
    # check that the keys are the expected ones, regardless of order
    assert sorted(keys) == sorted(keys_clean)
    # check that all dataframes are indexed by "timestamp", and that
    # this is a pandas.DatetimeIndex
    for sensor in keys:
        assert env_data[sensor].index.name == "timestamp"
        assert isinstance(env_data[sensor].index, pd.DatetimeIndex)
    assert energy_data.index.name == "timestamp"
    assert isinstance(energy_data.index, pd.DatetimeIndex)


def test_columns_clean_data():
    """
    Test that the processed dataframes contain the
    expected columns.
    """
    # note that in the way this is coded here the dataframes must have
    # at least the expected columns (they can also have extra columns).
    # Loop through every sensor (key) in the TRH data
    for sensor in keys:
        assert all(item in env_data[sensor].columns for item in colnames_env)
    # now test the energy data
    assert all(item in energy_data.columns for item in colnames_energy)


def test_timestamps_clean_data():
    """
    Test that the processed TRH and Energy dataframes
    have the same timestamps, that the timestamp vector is
    monotonically increasing and that timedelta between
    timestamps is unique.
    This function expects the dataframes to be indexed by
    timestamp.
    """
    # check that the timestamp vector is the same for all dataframes
    for ii in range(1, len(keys)):
        timestamp1 = env_data[keys[ii - 1]].index
        timestamp2 = env_data[keys[ii]].index
        assert timestamp2.equals(timestamp1)
    timestamp1 = energy_data.index
    assert timestamp2.equals(timestamp1)
    # check that the timestamp vector is monotonically increasing
    assert timestamp2.is_monotonic_increasing
    # check that the timedelta is unique
    timestamp2 = timestamp2.to_series()
    time_delta = timestamp2.diff()[1:]
    time_delta = pd.unique(time_delta)
    assert len(time_delta) == 1


def test_data_clean_data():
    """
    Test that the data in the processed dataframes
    is strictly equal to the expected one.
    """
    # compare sensor by sensor and column by column
    for sensor in keys:
        # compare timestamps (the dataframes are indexed by timestamp)
        assert env_data[sensor].index.equals(env_clean[sensor].index)
        # compare columns
        for column in colnames_env:
            assert env_data[sensor][column].equals(env_clean[sensor][column])
    # compare timestamps (the dataframes are indexed by timestamp)
    assert energy_data.index.equals(energy_clean.index)
    # compare columns
    for column in colnames_energy:
        assert energy_data[column].equals(energy_clean[column])
