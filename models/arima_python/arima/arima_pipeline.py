from arima.config import config
from statsmodels.tsa.statespace.sarimax import SARIMAX
import logging

logger = logging.getLogger(__name__)

arima_config = config(section="arima")


def train_arima(train_data):
    model = SARIMAX(
        train_data, order=arima_config["arima_order"], seasonal_order=["seasonal_order"]
    )
    model_fit = model.fit()  # fits the model by maximum likelihood via Kalman filter
    return model_fit


def forecast_arima(model_fit):
    forecast = model_fit.get_forecast(
        steps=48
    )  # TODO: this needs to forecast 48h into the future
    mean_forecast = forecast.predicted_mean  # forecast mean
    conf_int = forecast.conf_int()  # get confidence intervals of forecasts
    return mean_forecast, conf_int


def run_arima_pipeline(data):
    if arima_config["arima_order"] != (4, 1, 2):
        logger.warning(
            "The 'arima_order' setting in config.ini has been set to something different than (4, 1, 2)."
        )
