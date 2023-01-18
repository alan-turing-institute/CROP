import pandas as pd
import arima.cleanData as cleanData

# import the sample raw (un-processed) data
env_raw = pd.read_pickle("tests/data/aranet_trh_raw.pkl")
energy_raw = pd.read_pickle("tests/data/utc_energy_raw.pkl")

# import the processed data - this is the baseline we compare against
env_clean = pd.read_pickle("tests/data/aranet_trh_processed.pkl")
energy_clean = pd.read_pickle("tests/data/utc_energy_processed.pkl")

# set the list of temperature/rel humidity (TRH) sensors
# this is done here because "sensors_list" can be specified by the user via the config file
keys_clean = list(env_clean.keys())
cleanData.sensors_list = keys_clean

# column names TRH data should contain
colnames_env = list(env_clean[keys_clean[0]].columns)

# column names energy data should contain
colnames_energy = list(energy_clean.columns)

# call the function to process the raw data
env_data, energy_data = cleanData.cleanData(env_raw, energy_raw)
keys = list(env_data.keys())


def test_format_cleanData():
    """
    Test that the format of the post-processed data is
    the expected one.
    """
    # chect that variable types are correct
    assert isinstance(env_data, dict)
    for ii in range(0, len(keys)):
        assert isinstance(env_data[keys[ii]], pd.DataFrame)
    assert isinstance(energy_data, pd.DataFrame)
    # check that the keys are the expected ones
    assert all(item in keys for item in keys_clean)


def test_columns_cleanData():
    """
    Test that the post-processed dataframes contain the
    expected columns.
    """
    # loop through every sensor (key) in the TRH data
    for ii in range(0, len(keys)):
        assert all(item in env_data[keys[ii]].columns for item in colnames_env)
    # now test the energy data
    assert all(item in energy_data.columns for item in colnames_energy)


def test_timestamps_cleanData():
    """
    Test that the post-processed TRH and Energy dataframes
    have the same timestamps, that the timestamp vector is
    monotonically increasing and that timedelta between
    timestamps is unique.
    """
    # check that the timestamp vector is the same for all data
    for ii in range(1, len(keys)):
        timestamp1 = env_data[keys[ii - 1]].timestamp
        timestamp2 = env_data[keys[ii]].timestamp
        assert timestamp2.equals(timestamp1)
    timestamp1 = energy_data.timestamp
    assert timestamp2.equals(timestamp1)
    # check that the timestamp vector is monotonically increasing
    assert timestamp2.is_monotonic
    # check that the timedelta is unique
    time_delta = timestamp2.diff()[1:]
    time_delta = pd.unique(time_delta)
    assert len(time_delta) == 1
