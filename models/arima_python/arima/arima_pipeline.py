from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResultsWrapper
from datetime import timedelta
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
import numpy as np
from copy import deepcopy
import pandas as pd
import logging
from typing import Tuple, Union

try:
    from arima.config import config
except ModuleNotFoundError:
    from models.arima_python.arima.config import config


logger = logging.getLogger(__name__)

arima_config = config(section="arima")


def get_forecast_timestamp(data: pd.Series) -> pd.Timestamp:
    """
    Return the end-of-forecast timestamp.

    Parameters:
        data: pandas Series containing a time series.
            Must be indexed by timestamp.

    Returns:
        forecast_timestamp: end-of-forecast timestamp,
            calculated by adding the `hours_forecast`
            parameter of config.ini to the last timestamp
            of `data`.
    """
    if arima_config["hours_forecast"] <= 0:
        logger.error(
            "The 'hours_forecast' parameter in config.ini must be greater than zero."
        )
        raise Exception
    end_of_sample_timestamp = data.index[-1]
    forecast_timestamp = end_of_sample_timestamp + timedelta(
        hours=arima_config["hours_forecast"]
    )
    return forecast_timestamp


def fit_arima(train_data: pd.Series) -> SARIMAXResultsWrapper:
    """
    Fit a SARIMAX statsmodels model to a
    training dataset (time series).
    The model parameters are specified through the
    `arima_order`, `seasonal_order` and `trend`
    settings in config.ini.

    Parameters:
        train_data: a pandas Series containing the
            training data on which to fit the model.

    Returns:
        model_fit: the fitted model, which can now be
            used for forecasting.
    """
    model = SARIMAX(
        train_data,
        order=arima_config["arima_order"],
        seasonal_order=arima_config["seasonal_order"],
        trend=arima_config["trend"],
    )
    model_fit = model.fit(
        disp=False
    )  # fits the model by maximum likelihood via Kalman filter
    return model_fit


def forecast_arima(
    model_fit: SARIMAXResultsWrapper, forecast_timestamp: pd.Timestamp
) -> Tuple[pd.Series, pd.DataFrame]:
    """
    Produce a forecast given a trained SARIMAX model.

    Arguments:
        model_fit: the SARIMAX model fitted to training data.
            This is the output of `fit_arima`.
        forecast_timestamp: the end-of-forecast timestamp.

    Returns:
        mean_forecast: the forecast mean. A pandas Series, indexed
            by timestamp.
        conf_int: the lower and upper bounds of the confidence
            intervals of the forecasts. A pandas Dataframe, indexed
            by timestamp. Specify the confidence level through parameter
            `alpha` in config.ini.
    """
    alpha = arima_config["alpha"]
    forecast = model_fit.get_forecast(steps=forecast_timestamp).summary_frame(
        alpha=alpha
    )
    mean_forecast = forecast["mean"]  # forecast mean
    conf_int = forecast[
        ["mean_ci_lower", "mean_ci_upper"]
    ]  # get confidence intervals of forecasts
    return mean_forecast, conf_int


def construct_cross_validator(
    data: pd.Series, train_fraction: float = 0.8, n_splits: int = 4
) -> TimeSeriesSplit:
    """
    Construct a time series cross validator (TSCV) object.

    Arguments:
        data: time series for which to construct the TSCV,
            as a pandas Series.
        train_fraction: fraction of `data` to use as the
            initial model training set. The remaining data
            will be used as the testing set in cross-validation.
        n_splits: number of splits/folds of the testing set
            for cross-validation.
    Returns:
        tscv: the TSCV object, constructed with
            sklearn.TimeSeriesSplit.
    """
    if (train_fraction < 0.5) or (train_fraction >= 1):
        logger.error(
            "The fraction of training data for cross-validation must be >= 0.5 and < 1."
        )
        raise ValueError
    n_obs = len(data)  # total number of observations
    n_obs_test = n_obs * (
        1 - train_fraction
    )  # total number of observations used for testing
    test_size = int(
        n_obs_test // n_splits
    )  # number of test observations employed in each fold
    if test_size < 1:
        logger.error(
            "A valid cross-validator cannot be built. The size of the test set is less than 1."
        )
        raise Exception
    tscv = TimeSeriesSplit(
        n_splits=n_splits, test_size=test_size
    )  # construct the time series cross-validator
    return tscv


def cross_validate_arima(
    data: pd.Series, tscv: TimeSeriesSplit, refit: bool = False
) -> dict:
    """
    Cross-validate a SARIMAX statsmodel model.

    Arguments:
        data: pandas Series containing the time series
            for which the SARIMAX model is built.
        tscv: the time series cross-validator object,
            returned by `construct_cross_validator`.
        refit: specify whether to refit the model
            parameters when new observations are added
            to the training set in successive cross-
            validation folds (True) or not (False).
            The default is False, as this is faster for
            large datasets.
    Returns:
        metrics: a dict containing two model metrics:
            "RMSE": the cross-validated root-mean-squared-error.
                See `sklearn.metrics.mean_squared_error`.
            "MAPE": the cross-validated mean-absolute-percentage-error.
                See `sklearn.metrics.mean_absolute_percentage_error`.
    """
    metrics = dict.fromkeys(["RMSE", "MAPE"])
    rmse = []  # this will hold the RMSE at each fold
    mape = []  # this will hold the MAPE score at each fold
    # loop through all folds
    for fold, (train_index, test_index) in enumerate(tscv.split(data)):
        cv_train, cv_test = (
            data.iloc[train_index],
            data.iloc[test_index],
        )  # train/test split for the current fold
        # only force model fitting in the first fold
        if fold == 0:
            model_fit = fit_arima(cv_train)
        # in all other folds, the model is refitted only if requested by the user
        # here we append to the current train set the test set of the previous fold
        else:
            if refit:
                model_fit = model_fit.append(cv_test_old, refit=True)
            else:
                model_fit = model_fit.extend(
                    cv_test_old
                )  # extend is faster than append with refit=False
        forecast = model_fit.forecast(
            steps=len(test_index)
        )  # compute the forecast for the test sample of the current fold
        rmse.append(
            mean_squared_error(cv_test.values, forecast.values, squared=False)
        )  # compute the RMSE for the current fold
        mape.append(
            mean_absolute_percentage_error(cv_test.values, forecast.values)
        )  # compute the MAPE for the current fold
        cv_test_old = deepcopy(cv_test)

    metrics["RMSE"] = np.mean(
        rmse
    )  # the cross-validated RMSE: the mean RMSE across all folds
    metrics["MAPE"] = np.mean(
        mape
    )  # the cross-validated MAPE: the mean MAPE across all folds
    return metrics


def arima_pipeline(
    data: pd.Series,
) -> Tuple[pd.Series, pd.DataFrame, Union[dict, None]]:
    """
    Run the ARIMA model pipeline, using the SARIMAX model provided
    by the `statsmodels` library. This is the parent function of
    the `arima_pipeline` module.
    The SARIMAX model parameters can be specified via the
    `config.ini` file.

    Arguments:
        data: the time series on which to train the SARIMAX model,
            as a pandas Series indexed by timestamp.
    Returns:
        mean_forecast: a pandas Series, indexed by timestamp,
            containing the forecast mean. The number of hours to
            forecast into the future can be specified through the
            `config.ini` file.
        conf_int: a pandas Dataframe, indexed by timestamp, containing
            the lower an upper confidence intervals for the forecasts.
        metrics: a dictionary containing the cross-validated root-mean-
            squared-error (RMSE) and mean-absolute-percentage-error (MAPE)
            for the fitted SARIMAX model. If the user requests not to perform
            cross-validation through the `config.ini` file, `metrics`
            is assigned `None`.
    """
    if not isinstance(data.index, pd.DatetimeIndex):
        logger.error(
            "The time series on which to train the ARIMA model must be indexed by timestamp."
        )
        raise ValueError
    if arima_config["arima_order"] != (4, 1, 2):
        logger.warning(
            "The 'arima_order' setting in config.ini has been set to something different than (4, 1, 2)."
        )
    if arima_config["seasonal_order"] != (1, 1, 0, 24):
        logger.warning(
            "The 'seasonal_order' setting in config.ini has been set to something different than (1, 1, 0, 24)."
        )
    if arima_config["hours_forecast"] != 48:
        logger.warning(
            "The 'hours_forecast' setting in config.ini has been set to something different than 48."
        )
    # perform time series cross-validation if requested by the user
    cross_validation = arima_config["perform_cv"]
    if cross_validation:
        refit = arima_config["cv_refit"]
        if refit:
            logger.info("Running time series cross-validation WITH parameter refit...")
        else:
            logger.info(
                "Running time series cross-validation WITHOUT parameter refit..."
            )
        try:
            tscv = construct_cross_validator(data)
            try:
                metrics = cross_validate_arima(data, tscv, refit=refit)
            except:
                logger.warning(
                    "Could not perform cross-validation. Continuing without ARIMA model testing."
                )
                metrics = None
            else:
                logger.info(
                    "Done running cross-validation. The CV root-mean-squared-error is: {0:.2f}. The CV mean-absolute-percentage-error is: {1:.3f}".format(
                        metrics["RMSE"], metrics["MAPE"]
                    )
                )
        except:
            logger.warning(
                "Could not build a valid cross-validator. Continuing without ARIMA model testing."
            )
            metrics = None
    else:
        metrics = None
    # fit the model and compute the forecast
    logger.info("Fitting the model...")
    model_fit = fit_arima(data)
    logger.info("Done fitting the model.")
    forecast_timestamp = get_forecast_timestamp(data)
    logger.info("Computing forecast...")
    logger.info(
        "Start of forecast timestamp: {0}. End of forecast timestamp: {1}".format(
            data.index[-1], forecast_timestamp
        )
    )
    mean_forecast, conf_int = forecast_arima(model_fit, forecast_timestamp)
    logger.info("Done forecasting.")

    return mean_forecast, conf_int, metrics
