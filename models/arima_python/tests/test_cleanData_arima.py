import pandas as pd
import arima.cleanData as cleanData
import arima.config as config

# import the sample raw (un-processed) data
env_raw = pd.read_pickle("tests/data/aranet_trh_raw.pkl")
energy_raw = pd.read_pickle("tests/data/utc_energy_raw.pkl")

# import the processed data
env_clean = pd.read_pickle("tests/data/aranet_trh_processed.pkl")
energy_clean = pd.read_pickle("tests/data/utc_energy_processed.pkl")
