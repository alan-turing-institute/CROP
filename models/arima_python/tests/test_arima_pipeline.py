import pandas as pd
import arima.arima_pipeline as arima_pipeline
from statsmodels.tsa.statespace.sarimax import SARIMAXResultsWrapper

# import the pickle file used for ARIMA code testing
# the pickle file contains a dictionary - see tests/data/README.md for details
dataset = pd.read_pickle("tests/data/airline_dataset_arima.pkl")
airline_dataset = dataset["dataset"]  # this is the airline dataset
train_index = dataset["train_index"]  # indices of train data
test_index = dataset["test_index"]  # indices of test data

# set the ARIMA model parameters for the airline time-series
arima_pipeline.arima_config["arima_order"] = (2, 1, 0)
arima_pipeline.arima_config["seasonal_order"] = (1, 1, 0, 12)
arima_pipeline.arima_config["trend"] = []


def test_get_forecast_timestamp():
    """
    Test that the returned end-of-forecast timestamp
    is the expected one.
    """
    start_timestamp = airline_dataset.iloc[train_index].index[-1]
    end_timestamp = airline_dataset.index[-1]
    delta_time = end_timestamp - start_timestamp
    delta_time = delta_time.total_seconds()  # total timedetla in seconds
    delta_time = delta_time / 3600  # total timedelta in hours
    arima_pipeline.arima_config["hours_forecast"] = delta_time
    forecast_timestamp = arima_pipeline.get_forecast_timestamp(
        airline_dataset.iloc[train_index]
    )
    assert forecast_timestamp == end_timestamp


def test_arima_model_fit():
    train_data = airline_dataset["lnair"].iloc[train_index]
    model_fit = arima_pipeline.train_arima(train_data)
    assert isinstance(model_fit, SARIMAXResultsWrapper)
