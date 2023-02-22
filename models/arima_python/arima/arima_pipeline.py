from arima.config import config
from statsmodels.tsa.statespace.sarimax import SARIMAX
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

arima_config = config(section="arima")


def get_end_of_forecast_timestamp(data):
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
    )
    model_fit = model.fit()  # fits the model by maximum likelihood via Kalman filter
    return model_fit


def forecast_arima(model_fit, forecast_timestamp):
    forecast = model_fit.get_forecast(steps=forecast_timestamp)
    mean_forecast = forecast.predicted_mean  # forecast mean
    conf_int = forecast.conf_int()  # get confidence intervals of forecasts
    return mean_forecast, conf_int


def arima_pipeline(data, cross_validation=True):
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
    # if cross_validation:
