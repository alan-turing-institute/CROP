import pandas as pd
import arima.arima_pipeline as arima_pipeline
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResultsWrapper
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

# import the pickle file used for ARIMA code testing
# the pickle file contains a dictionary - see tests/data/README.md for details
dataset = pd.read_pickle("tests/data/airline_dataset_arima.pkl")
airline_dataset = dataset["dataset"]  # this is the airline dataset
train_index = dataset["train_index"]  # indices of train data
test_index = dataset["test_index"]  # indices of test data

# set the ARIMA model parameters for the airline time-series
arima_order = (2, 1, 0)
seasonal_order = (1, 1, 0, 12)
trend = []
arima_pipeline.arima_config["arima_order"] = arima_order
arima_pipeline.arima_config["seasonal_order"] = seasonal_order
arima_pipeline.arima_config["trend"] = trend


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


def test_arima_cross_validation():
    # check that the cross-validator constructor returns the expected train/test split
    n_obs = 100
    train_fraction = 0.6
    n_splits = 2
    data = airline_dataset.iloc[:n_obs]
    # these are the indices of training data we would expect given the above parameters
    expected_train_index = dict.fromkeys(list(range(n_splits)))
    expected_train_index[0] = np.arange(60)
    expected_train_index[1] = np.arange(80)
    # these are the indices of testing data we would expect given the above parameters
    expected_test_index = dict.fromkeys(list(range(n_splits)))
    expected_test_index[0] = np.arange(60, 80)
    expected_test_index[1] = np.arange(80, 100)
    # construct the cross-validator
    tscv = arima_pipeline.construct_cross_validator(
        data, train_fraction=train_fraction, n_splits=n_splits
    )
    # these are the indices of test/train split returned by the cross-validator constructor
    actual_train_index = dict()
    actual_test_index = dict()
    for fold, (train_index, test_index) in enumerate(tscv.split(data)):
        actual_train_index[fold] = train_index
        actual_test_index[fold] = test_index
    # assert that the actual and expected indices are equal
    np.testing.assert_equal(actual_train_index, expected_train_index, verbose=False)
    np.testing.assert_equal(actual_test_index, expected_test_index, verbose=False)

    # now test that the returned model metrics are correct
    train_index = expected_train_index
    test_index = expected_test_index
    model = SARIMAX(
        data["lnair"].iloc[train_index[0]],
        order=arima_order,
        seasonal_order=seasonal_order,
        trend=trend,
    )
    model_fit = model.fit(disp=False)
    forecast_fold_0 = model_fit.forecast(steps=len(test_index[0]))
    model_fit = model_fit.extend(data["lnair"].iloc[test_index[0]])
    forecast_fold_1 = model_fit.forecast(steps=len(test_index[1]))
    rmse = np.mean(
        [
            mean_squared_error(
                data["lnair"].iloc[test_index[0]],
                forecast_fold_0,
                squared=False,
            ),
            mean_squared_error(
                data["lnair"].iloc[test_index[1]],
                forecast_fold_1,
                squared=False,
            ),
        ]
    )
    r2 = np.mean(
        [
            r2_score(
                data["lnair"].iloc[test_index[0]],
                forecast_fold_0,
            ),
            r2_score(
                data["lnair"].iloc[test_index[1]],
                forecast_fold_1,
            ),
        ]
    )
    metrics = arima_pipeline.cross_validate_arima(data["lnair"], tscv, refit=False)
    assert np.isclose(rmse, metrics["RMSE"], atol=1e-06)
    assert np.isclose(r2, metrics["R2"], atol=1e-06)
