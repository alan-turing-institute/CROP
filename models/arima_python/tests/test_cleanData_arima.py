import pandas as pd
import arima.cleanData as cleanData
import arima.config as config

# import the sample raw (un-processed) data
env_raw = pd.read_pickle("tests/data/aranet_trh_raw.pkl")
energy_raw = pd.read_pickle("tests/data/utc_energy_raw.pkl")

# import the processed data - this is the baseline we compare against
env_clean = pd.read_pickle("tests/data/aranet_trh_processed.pkl")
energy_clean = pd.read_pickle("tests/data/utc_energy_processed.pkl")

# set the list of temperature/rel humidity (TRH) sensors
keys_clean = list(env_clean.keys())
cleanData.sensors_list = keys_clean

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
    # expected column names for TRH data
    colnames = [
        "timestamp",
        "temperature",
        "humidity",
    ]
    # loop through every sensor (key) in the TRH data
    for ii in range(0, len(keys)):
        assert all(item in env_data[keys[ii]].columns for item in colnames)
    # expected column names for energy data
    colnames = [
        "timestamp",
        "EnergyCC",
        "EnergyCP",
        "EnergyCC_MA",
        "EnergyCP_MA",
    ]
    assert all(item in energy_data for item in colnames)
