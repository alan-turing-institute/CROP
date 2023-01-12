import pandas as pd
import arima.cleanData as cleanData
import arima.config as config

# import the sample raw (un-processed) data
env_raw = pd.read_pickle("tests/data/aranet_trh_raw.pkl")
energy_raw = pd.read_pickle("tests/data/utc_energy_raw.pkl")

# import the processed data
env_clean = pd.read_pickle("tests/data/aranet_trh_processed.pkl")
energy_clean = pd.read_pickle("tests/data/utc_energy_processed.pkl")

# set the list of temperature/rel humidity sensors
keys_clean = list(env_clean.keys())
cleanData.sensors_list = keys_clean

env_data, energy_data = cleanData.cleanData(env_raw, energy_raw)


def test_format_cleanData():
    """
    Test that the format of the post-processed data is
    the expected one.
    """
    # chect that variable types are correct
    assert isinstance(env_data, dict)
    keys = list(env_data.keys())
    for ii in range(0, len(keys)):
        assert isinstance(env_data[keys[ii]], pd.DataFrame)
    assert isinstance(energy_data, pd.DataFrame)
    # check that the keys are the expected ones
    assert all(item in keys for item in keys_clean)
