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
    """
    Replace missing values in a time series with "typically observed"
    values. This function makes use of the `days_interval` and
    `weekly_seasonality` parameters in config.ini.
    Note that there needs to be sufficient data in the input time series
    in order to compute typically-observed values. Otherwise, missing
    observations will not be replaced.
    Three different seasonalities are assumed in the data by default:
    daily, weekly, and pseudo-season. These seasonalities are employed
    to compute the typically-observed values that will replace missing
    values. The `weekly_seasonality` parameter can be set to `False` in
    order to remove the weekly-seasonality assumption, and the time
    interval of the pseudo-season can be modified through `days_interval`.

    Parameters:
        data: a time series as a pandas Series, potentially containing
            missing values. Must be indexed by timestamp.

    Returns:
        data: the input time series as a pandas Series, where any missing
            values have been replaced with typically-observed values.
    """
    if not (isinstance(data, pd.Series) and isinstance(data.index, pd.DatetimeIndex)):
        logger.error(
            "The input time series must be a pandas Series indexed by timestamp."
        )
        raise ValueError
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
    # otherwise, only consider daily and pseudo-season seasonality
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


def prepare_data(
    env_data: dict, energy_data: pd.DataFrame
) -> tuple[dict, pd.DataFrame]:
    """
    Parent function of this module. Prepares the data in order to feed it into
    the ARIMA pipeline. Parameters relevant to this function in config.ini are
    `farm_cycle_start`, `days_interval` and `weekly_seasonality`. The last two
    are employed to replace missing observations.

    Parameters:
        env_data: this is the first output of `clean_data.clean_data`.
            A dictionary containing temperature and humidity data for
            each of the sensors, in the form of a pandas DataFrame.
        energy_data: this is the second output of `clean_data.clean_data`.
            A pandas DataFrame containing electricity consumption data.

    Returns:
        env_data: a dictionary with the same keys as the input `env_data`.
            Each key is named after the corresponding sensor. The DataFrames
            contained in this dictionary are indexed by timestamp and are
            processed so that the timestamps are in agreement with the
            start of the farm cycle, specified through the parameter
            `farm_cycle_start` in config.ini. Missing observations will be
            replaced by "typically observed" values if there is enough data
            and the combination of parameters `days_interval` and `weekly_seasonality`
            allows it.
        energy_data: a pandas DataFrame, indexed by timestamp, containing the
            electricity consumption data, and processed in the same way as
            `env_data`. Additionally, the column `EnergyCP` will be multiplied
            by an "hourly consumption factor", depending on the timedelta between
            successive observations and the `freq_energy_data` parameter in
            config.ini.
    """
    # obtain the standardized timestamp.
    # note that both `env_data` and `energy_data` are indexed by the same timestamps.
    timestamp_standardized = standardize_timestamp(energy_data.index[-1])
    # keep only the observations whose timestamp is smaller or equal to the
    # standardized timestamp
    keys_env_data = list(env_data.keys())
    for key in keys_env_data:
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

    # if there are any missing values in the `temperature` time series of `env_data`
    # or the `EnergyCP` time series of `energy_data`, replace them with typically
    # observed values. Note that if there is not enough data to compute typically
    # observed values, missing observations will not be replaced.
    for key in keys_env_data:
        temperature = env_data[key]["temperature"]
        if temperature.isna().any():
            env_data[key]["temperature"] = impute_missing_values(temperature)
    energy = energy_data["EnergyCP"]
    if energy.isna().any():
        energy_data["EnergyCP"] = impute_missing_values(energy)

    return env_data, energy_data
