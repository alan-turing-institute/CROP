import pandas as pd
import arima.arima_pipeline as arima_pipeline
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResultsWrapper
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
import numpy as np
import pytest

# import the pickle file used for ARIMA code testing
# the pickle file contains a dictionary - see tests/data/README.md for details
dataset = pd.read_pickle("tests/data/airline_dataset_arima.pkl")
airline_dataset = dataset["dataset"]  # this is the full airline dataset
train_index = dataset["train_index"]  # indices of train data (70%)
test_index = dataset["test_index"]  # indices of test data (30%)
airline_forecast = dataset[
    "forecasts"
]  # this is a pre-computed forecast of the test data

# set the ARIMA model parameters for the airline time-series
# see prepare_airline_dataset.ipynb for details
arima_order = (2, 1, 0)
seasonal_order = (1, 1, 0, 12)
trend = []
alpha = 0.05
arima_pipeline.arima_config["arima_order"] = arima_order
arima_pipeline.arima_config["seasonal_order"] = seasonal_order
arima_pipeline.arima_config["trend"] = trend
arima_pipeline.arima_config["alpha"] = alpha


def set_hours_forecast(start_timestamp, end_timestamp):
    """
    Given a starting and an ending timestamps, calculate
    the timedelta between them and set this timedelta as
    the "hours_forecast" parameter of config.ini.
    """
    delta_time = end_timestamp - start_timestamp
    delta_time = delta_time.total_seconds()  # total timedetla in seconds
    delta_time = delta_time / 3600  # total timedelta in hours
    arima_pipeline.arima_config["hours_forecast"] = delta_time


def test_get_forecast_timestamp():
    """
    Test that the returned end-of-forecast timestamp
    is the expected one.
    """
    # first, set the number of hours to forecast into the future
    start_timestamp = airline_dataset.iloc[train_index].index[-1]
    end_timestamp = airline_dataset.iloc[test_index].index[-1]
    set_hours_forecast(start_timestamp, end_timestamp)
    # now check if the end-of-forecast timestamp is produced
    # correctly
    forecast_timestamp = arima_pipeline.get_forecast_timestamp(
        airline_dataset.iloc[train_index]
    )
    assert forecast_timestamp == end_timestamp


def test_fit_forecast_arima():
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
    forecast_timestamp = airline_dataset.iloc[test_index].index[
        -1
    ]  # perform forecast up to this date
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
    ]  # lower and upper bounds of the confidence intervals
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


def test_construct_cross_validator():
    """
    Check that the cross-validator constructor
    returns the expected train/test split of an
    input dataset.
    """
    n_obs = 100
    train_fraction = 0.6  # fraction of training data in the first CV fold (fold 0)
    n_splits = 2  # number of splits/folds for CV
    data = airline_dataset.iloc[:n_obs]
    # these are the indices of training data we would expect given the above specification
    expected_train_index = dict.fromkeys(list(range(n_splits)))
    expected_train_index[0] = np.arange(60)  # fold 0
    expected_train_index[1] = np.arange(80)  # fold 1
    # these are the indices of testing data we would expect given the above specification
    expected_test_index = dict.fromkeys(list(range(n_splits)))
    expected_test_index[0] = np.arange(60, 80)  # fold 0
    expected_test_index[1] = np.arange(80, 100)  # fold 1
    # construct the cross-validator
    tscv = arima_pipeline.construct_cross_validator(
        data, train_fraction=train_fraction, n_splits=n_splits
    )
    # below are the indices of test/train split returned by the cross-validator constructor
    actual_train_index = dict()
    actual_test_index = dict()
    for fold, (train_index, test_index) in enumerate(tscv.split(data)):
        actual_train_index[fold] = train_index
        actual_test_index[fold] = test_index
    # assert that the actual and expected indices are equal
    np.testing.assert_equal(actual_train_index, expected_train_index, verbose=False)
    np.testing.assert_equal(actual_test_index, expected_test_index, verbose=False)


def compute_model_metrics(data, model_fit, test_index):
    """
    Compute cross-validated model metrics (RMSE and MAPE).

    Parameters:
        data: pandas Series containing the time series.
        model_fit: the fit to a SARIMAX statsmodels model.
        test_index: dictionary containing indices of test
            data at successive folds.
    Returns:
        rmse: root-mean-square-error, averaged across all CV folds.
        mape: mean-absolute-percentage-error, averaged across all CV folds.
    """
    forecasts = dict.fromkeys(list(test_index.keys()))
    rmse = []
    mape = []
    for fold in list(forecasts.keys()):
        forecasts[fold] = model_fit.forecast(steps=len(test_index[fold]))
        model_fit = model_fit.extend(data.iloc[test_index[fold]])
        rmse.append(
            mean_squared_error(
                data.iloc[test_index[fold]].values,
                forecasts[fold].values,
                squared=False,
            )
        )
        mape.append(
            mean_absolute_percentage_error(
                data.iloc[test_index[fold]].values,
                forecasts[fold].values,
            )
        )
    rmse = np.mean(rmse)
    mape = np.mean(mape)
    return rmse, mape


def test_cross_validate_arima():
    """
    Test that the calculation of cross-validated
    model metrics (RMSE and MAPE) is done correctly.
    """
    data = airline_dataset["lnair"]
    train_fraction = 0.7  # fraction of training data in the first CV fold (fold 0)
    n_splits = 3  # number of splits/folds for CV
    # build the cross-validator, and get the train/test indices
    tscv = arima_pipeline.construct_cross_validator(
        data, train_fraction=train_fraction, n_splits=n_splits
    )
    train_index = dict()
    test_index = dict()
    for fold, (train_index_fold, test_index_fold) in enumerate(tscv.split(data)):
        train_index[fold] = train_index_fold
        test_index[fold] = test_index_fold
    # create and fit the SARIMAX model with the 0-fold training set
    model = SARIMAX(
        data.iloc[train_index[0]],
        order=arima_order,
        seasonal_order=seasonal_order,
        trend=trend,
    )
    model_fit = model.fit(disp=False)
    # compute the CV model metrics, and check that they are close
    # to the values returned by the arima pipeline
    rmse, mape = compute_model_metrics(data, model_fit, test_index)
    metrics = arima_pipeline.cross_validate_arima(data, tscv, refit=False)
    assert np.isclose(rmse, metrics["RMSE"], atol=1e-04)
    assert np.isclose(mape, metrics["MAPE"], atol=1e-04)
    # finally, just as a sanity check, verify that both RMSE and MAPE
    # are >= 0.0
    assert metrics["RMSE"] >= 0.0
    assert metrics["MAPE"] >= 0.0


def test_arima_pipeline():
    """
    Test that the arima pipeline produces the
    expected (pre-computed) forecasts.
    """
    # no need to perform cross-validation now - switch off
    arima_pipeline.arima_config["perform_cv"] = False
    # specify the training data and set the number of
    # hours to forecast into the future
    train_data = airline_dataset["lnair"].iloc[train_index]
    start_timestamp = airline_dataset["lnair"].iloc[train_index].index[-1]
    end_timestamp = airline_dataset["lnair"].iloc[test_index].index[-1]
    set_hours_forecast(start_timestamp, end_timestamp)
    # now run the arima pipeline on the training data
    # to produce the forecast
    mean_forecast, conf_int = arima_pipeline.arima_pipeline(train_data)[:2]
    # assert that the mean forecast and the confidence
    # intervals are the expected (pre-computed) ones
    assert np.isclose(mean_forecast, airline_forecast["mean"], atol=1e-3).all()
    assert np.isclose(
        conf_int, airline_forecast[["mean_ci_lower", "mean_ci_upper"]], atol=1e-03
    ).all()
    # finally check that a ValueError is raised if the input
    # time series is not indexed by timestamp
    with pytest.raises(ValueError):
        train_data.reset_index(drop=True, inplace=True)
        arima_pipeline.arima_pipeline(train_data)
