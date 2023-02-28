import pandas as pd
import arima.arima_pipeline as arima_pipeline
from statsmodels.tsa.statespace.sarimax import SARIMAXResultsWrapper
import pandas as pd

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


def test_arima_fit_forecast():
    """
    Test that the model fit is a valid SARIMAX results object,
    and that a valid forecast mean and confidence intervals
    are returned.
    """
    train_data = airline_dataset["lnair"].iloc[
        train_index
    ]  # this is the data we fit the model on
    model_fit = arima_pipeline.fit_arima(
        train_data
    )  # returns the model fit - pytest will raise error if convergence warnings
    assert isinstance(
        model_fit, SARIMAXResultsWrapper
    )  # check that model fit is of the correct type
    forecast_timestamp = airline_dataset.index[-1]  # perform forecast up to this date
    forecast = arima_pipeline.forecast_arima(
        model_fit, forecast_timestamp
    )  # compute the forecast
    # check that the returned forecast object is the expected one
    assert len(forecast) == 2  # should contain two objects
    assert isinstance(
        forecast[0], pd.Series
    )  # the first one is a series containing the forecast mean
    assert isinstance(
        forecast[1], pd.DataFrame
    )  # the second one is a dataframe containing the confidence intervals
    assert list(forecast[1].columns) == [
        "mean_ci_lower",
        "mean_ci_upper",
    ]  # lower and upper bounds
    assert isinstance(
        forecast[0].index, pd.DatetimeIndex
    )  # should be indexed by timestamp
    assert isinstance(forecast[1].index, pd.DatetimeIndex)
    assert not forecast[0].isna().any()  # check that there are no missing values
    assert not any(forecast[1].isna().any())
    # check that the mean forecast is always within the bounds of the confidence intervals
    assert all(
        [
            all(forecast[1]["mean_ci_lower"] < forecast[0].values),
            all(forecast[1]["mean_ci_upper"] > forecast[0].values),
        ]
    )
