from .config import config
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

constants = config(section="constants")
data_config = config(section="data")
arima_config = config(section="arima")


def standardize_timestamp(timestamp: datetime) -> datetime:
    """
    Standardize the input timestamp according to the
    time at which the farm daily cycle starts.
    Specify the start time of the farm cycle using the
    `farm_cycle_start` parameter in config.ini.

    Parameters:
        timestamp: a datetime object or equivalent
            (e.g. pandas Timestamp).

    Returns:
        timestamp: the input timestamp standardised according
            the time at which the farm cycle starts.
            - If the time of the input timestamp is >=
            `farm_cycle_start`, the output timestamp is the date
            of the input timestamp at time `farm_cycle_start`.
            - If the time of the input timestamp is <=
            (`farm_cycle_start` - 12 hours), the output timestamp
            is the date of the input timestamp minus one day at
            time `farm_cycle_start`.
            - Otherwise, the output timestamp is the date of the
            input timestamp at time (`farm_cycle_start` - 12 hours).
    """
    farm_cycle_start = arima_config[
        "farm_cycle_start"
    ]  # time at which the farm cycle starts
    # parse string into a datetime object
    farm_cycle_start = datetime.strptime(farm_cycle_start, "%Hh%Mm%Ss")
    farm_cycle_start = datetime.combine(timestamp.date(), farm_cycle_start.time())

    if timestamp >= farm_cycle_start:
        timestamp = farm_cycle_start
    elif timestamp <= (
        farm_cycle_start - timedelta(hours=constants["hrs_per_day"] / 2)
    ):
        timestamp = datetime.combine(
            (timestamp - timedelta(days=1)).date(),
            farm_cycle_start.time(),
        )
    else:
        timestamp = farm_cycle_start - timedelta(hours=constants["hrs_per_day"] / 2)
    return timestamp


def break_up_timestamp(data: pd.DataFrame, days_interval: int) -> pd.DataFrame:
    """
    Given an input pandas DataFrame indexed by timestamp
    and a time interval in days, break up the timestamps into
    time of the day, day of the week and a pseudo-season.

    Parameters:
        data: pandas DataFrame indexed by timestamp.
        days_interval: number of days of the time interval that
            defines the pseudo-season.

    Returns:
        data: the input pandas DataFrame with additional columns:
            - `time`: the time of the day, as a `datetime.time` object.
            - `weekday`: the day of the week with Monday=0, Sunday=6.
            - `pseudo_season`: identifies timestamps belonging to the
                same pseudo season based on the interval specified through
                `days_interval`.
    """
    # create the time-of-the-day and day-of-the-week columns
    timestamps = data.index
    data["time"] = timestamps.time
    data["weekday"] = timestamps.weekday
    # now create the pseudo-season, based on the specified interval
    delta_time = timestamps - timestamps[0]
    delta_time = delta_time.to_pytimedelta()
    interval = timedelta(days=days_interval)
    data["pseudo_season"] = delta_time // interval  # floor division
    return data


def impute_missing_values(data: pd.Series) -> pd.Series:
    index_name = data.index.name  # get the index name - should be `timestamp`
    data = data.to_frame()  # first convert Series to DataFrame
    days_interval = arima_config["days_interval"]
    data = break_up_timestamp(data, days_interval)
    # compute the mean value for the groups, excluding missing values.
    weekly_seasonality = arima_config["weekly_seasonality"]
    # if the user has requested to consider weekly seasonality:
    if weekly_seasonality:
        if days_interval < 30:
            logger.error(
                """
                If the 'weekly_seasonality' parameter in config.ini is set to `True`,
                the 'days_interval' parameter must be >= 30.
                """
            )
            raise ValueError
        # the resulting DataFrame will be multi-indexed by `pseudo-season`,
        # `weekday` and `time`.
        mean_values = data.groupby(["pseudo_season", "weekday", "time"]).mean()
        # elevate the index (the timestamps) of the input data to a column
        data = data.reset_index()
        # set the index to `pseudo_season`, `weekday` and `time`
        data.set_index(["pseudo_season", "weekday", "time"], inplace=True)
    # otherwise, only consider hourly and pseudo-season seasonality
    else:
        data.drop(columns="weekday", inplace=True)
        # the resulting DataFrame will be multi-indexed by `pseudo-season`
        # and `time`
        mean_values = data.groupby(["pseudo_season", "time"]).mean()
        # elevate the index (the timestamps) of the input data to a column
        data = data.reset_index()
        # set the index to `pseudo_season` and `time`
        data.set_index(["pseudo_season", "time"], inplace=True)
    # replace missing values with the computed mean values.
    # `DataFrame.update` modifies in-place, and aligns on indices.
    data.update(mean_values, overwrite=False)
    # now reset the index to be the timestamp column and make
    # sure that the rows are sorted in ascending order of index
    data.set_index(index_name, inplace=True)
    data.sort_index(ascending=True, inplace=True)
    data = data.squeeze()  # convert DataFrame back to Series
    return data


def prepare_data(env_data: dict, energy_data: pd.DataFrame):
    # obtain the standardized timestamp.
    # note that both `env_data` and `energy_data` are indexed by the same timestamps.
    timestamp_standardized = standardize_timestamp(energy_data.index[-1])
    # keep only the observations whose timestamp is smaller or equal to the
    # standardized timestamp
    keys = list(env_data.keys())
    for key in keys:
        env_data[key].drop(
            env_data[key][env_data[key].index > timestamp_standardized].index,
            inplace=True,
        )
    energy_data.drop(
        energy_data[energy_data.index > timestamp_standardized].index,
        inplace=True,
    )
    # compute the total hourly energy consumption, given the sampling frequency
    # of the `utc_energy_data` table
    freq_energy_data = data_config["freq_energy_data"]
    # parse string into datetime object
    freq_energy_data = datetime.strptime(freq_energy_data, "%Hh%Mm%Ss")
    # calculate total time between samples in seconds
    freq_energy_data = timedelta(
        hours=freq_energy_data.hour,
        minutes=freq_energy_data.minute,
        seconds=freq_energy_data.second,
    )
    freq_energy_data = freq_energy_data.total_seconds()
    # now calculate the total hourly consumption, which in the original
    # R code only affected the `EnergyCP` column of `energy_data`
    hourly_consumption_factor = (
        constants["secs_per_min"] * constants["mins_per_hr"] / freq_energy_data
    )
    energy_data["EnergyCP"] = energy_data["EnergyCP"] * hourly_consumption_factor
