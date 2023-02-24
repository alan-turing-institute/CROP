from arima.config import config
from statsmodels.tsa.statespace.sarimax import SARIMAX
from datetime import timedelta
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)

arima_config = config(section="arima")


def get_forecast_timestamp(data):
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


def train_arima(train_data):
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


def forecast_arima(model_fit, forecast_timestamp):
    forecast = model_fit.get_forecast(steps=forecast_timestamp).summary_frame()
    mean_forecast = forecast["mean"]  # forecast mean
    conf_int = forecast[
        ["mean_ci_lower", "mean_ci_upper"]
    ]  # get confidence intervals of forecasts
    return mean_forecast, conf_int


def cross_validate_arima(data, train_fraction=0.8, n_splits=4, refit=False):
    metrics = dict.fromkeys(["RMSE", "R2"])
    n_obs = len(data)  # total number of observations
    n_obs_test = n_obs * (
        1 - train_fraction
    )  # total number of observations used for testing
    test_size = int(
        n_obs_test // n_splits
    )  # number of test observations employed in each fold
    tscv = TimeSeriesSplit(
        n_splits=n_splits, test_size=test_size
    )  # construct the time series cross-validator
    rmse = []  # this will hold the RMSE at each fold
    r2 = []  # this will hold the R2 score at each fold
    # loop through all folds
    for fold, (train_index, test_index) in enumerate(tscv.split(data)):
        cv_train, cv_test = (
            data.iloc[train_index],
            data.iloc[test_index],
        )  # train/test split for the current fold
        # only force model fitting in the first fold
        if fold == 0:
            model_fit = train_arima(cv_train)
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
            steps=test_size
        )  # compute the forecast for the test sample of the current fold
        rmse.append(
            np.sqrt(mean_squared_error(cv_test.values, forecast.values))
        )  # compute the RMSE for the current fold
        r2.append(
            r2_score(cv_test.values, forecast.values)
        )  # compute the R2 for the current fold
        cv_test_old = deepcopy(cv_test)

    metrics["RMSE"] = np.mean(
        rmse
    )  # the cross-validated RMSE: the mean RMSE across all folds
    metrics["R2"] = np.mean(r2)  # the cross-validated R2: the mean R2 across all folds
    return metrics


def arima_pipeline(data):
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
        metrics = cross_validate_arima(data, refit=refit)
        logger.info(
            "Done running cross-validation. The CV root-mean-square-error is: {0:.2f}. The CV R-squared score is: {1:.2f}".format(
                metrics["RMSE"], metrics["R2"]
            )
        )
    else:
        metrics = []
    # fit the model and compute the forecast
    logger.info("Fitting the model...")
    model_fit = train_arima(data)
    logger.info("Done fitting the model.")
    forecast_timestamp = get_forecast_timestamp(data)
    logger.info(
        "Computing forecast...End of forecast timestamp: {}".format(forecast_timestamp)
    )
    mean_forecast, conf_int = forecast_arima(model_fit, forecast_timestamp)
    logger.info("Done forecasting.")

    return mean_forecast, conf_int, metrics
