from .dataAccess import getTrainingData
from .config import config
import pandas as pd
import numpy as np

constants = config(section="constants")
sensors_list = config(section="sensors")
sensors_list = sensors_list["include_sensors"]


def timeVector(start, end, frequency="1H", offset=1):
    """
    Create a vector of increasing timestamps.

    Parameters:
        start: starting timestamp.
        end: end timestamp.
        frequency: delta between successive timestamps.
            The default is "1H".
        offset: date offset added to the starting timestamp,
            in hours. The default is 1.
    Returns:
        time_vector: a pandas dataframe, with a single column
            named "timestamp", containing the vector of increasing
            timestamps.
    """
    # create a Pandas fixed frequency DatetimeIndex
    time_vector = pd.date_range(
        start + pd.DateOffset(hours=offset),
        end,
        freq=frequency,
    )
    time_vector = time_vector.to_frame(index=False)
    # rename the column to "timestamp"
    time_vector.rename(
        columns={list(time_vector)[0]: "timestamp"},
        inplace=True,
    )
    return time_vector


def hourly_average_sensor(env_data, col_names, time_vector):
    """
    Split the pandas dataframe containing the environment data
    into the user-requested list of sensors, group by the column
    "timestamp_hour_plus_minus", and perform averaging of the
    requested columns.

    Parameters:
        env_data: pre-processed pandas dataframe containing the
            environment data.
        col_names: list containing the names of the columns on
            which to perform the averaging after grouping by the
            column "timestamp_hour_plus_minus".
        time_vector: pandas dataframe containing a vector of increasing
            timestamps. Only timestamps contained in "time_vector"
            will be returned in the output ("hour_averages").
    Returns:
        hour_averages: a dict with keys named after the user-requested
            sensors, containing the columns on which averaging has been
            performed. Note that the column "timestamp_hour_plus_minus"
            is renamed to "timestamp".
    """
    hour_averages = dict.fromkeys(
        sensors_list
    )  # creates empty dict with specified keys (requested sensors)
    keys = list(hour_averages.keys())
    grouped = env_data.groupby("name")  # group by sensor name
    for ii in range(len(hour_averages)):
        sensor = grouped.get_group(keys[ii])
        # group by column "timestamp_hour_plus_minus" and perform
        # averaging on the requested columns
        hour_averages[keys[ii]] = sensor.groupby(
            "timestamp_hour_plus_minus", as_index=False
        )[col_names].mean()
        # rename the column to "timestamp"
        hour_averages[keys[ii]].rename(
            columns={"timestamp_hour_plus_minus": "timestamp"},
            inplace=True,
        )
        # perform a left merge with "time_vector" so that only
        # timestamps contained in "time_vector" are retained
        hour_averages[keys[ii]] = pd.merge(
            time_vector,
            hour_averages[keys[ii]],
            how="left",
        )
    return hour_averages


def centeredMA(series: pd.Series, window: int = 3):
    """
    Compute a weighted centered moving average of a time series.

    Parameters:
        series: time series as a pandas series.
        window: size of the moving window (fixed number of
            observations used for each window). Must be an
            odd integer, so that the average is centered.
            The default value is 3.
    Returns:
        MA: the weighted centered moving averages, returned as a
            pandas series. NaNs are returned at both ends of the
            series, where the centered average cannot be computed
            depending on the specified window size.
    """
    if not (window % 2):
        raise Exception("The window must be an odd integer.")
    # calculate the weights for the weighted average
    n = window - 1
    weights = np.zeros(
        window,
    )
    weights[1:-1] = 1 / n
    weights[0] = 1 / (n * 2)
    weights[-1] = 1 / (n * 2)
    # calculate the weighted centered MA, returned as a
    # pandas series
    MA = series.rolling(window=window, center=True).apply(lambda x: np.sum(weights * x))
    MA.name = MA.name + "_MA"  # rename the series
    return MA


def cleanEnvData(env_data):
    # TODO: this is done in the original R code but not yet clear if necessary
    # insert a new column at the end of the dataframe, named "hour_truncated",
    # that takes the truncated hour from the "timestamp" column
    env_data.insert(
        len(env_data.columns),
        "hour_truncated",
        env_data.timestamp.dt.hour,
    )
    # TODO: this is done in the original R code but not yet clear if necessary
    # insert a new column at the end of the dataframe, named "hour_decimal",
    # that expresses the time of the "timestamp" column in decimal form
    env_data.insert(
        len(env_data.columns),
        "hour_decimal",
        env_data.timestamp.dt.hour
        + env_data.timestamp.dt.minute / constants["secs_per_min"],
    )
    # insert a new column at the end of the dataframe, named "timestamp_hour_floor",
    # that rounds the timestamp by flooring to hour precision
    env_data.insert(
        len(env_data.columns),
        "timestamp_hour_floor",
        env_data.timestamp.dt.floor("h"),
    )
    # create a new column, named "timedelta_in_secs", that expresses
    # the time difference, in seconds, between a timestamp and
    # itself rounded to the hour
    env_data["timedelta_in_secs"] = env_data["timestamp"].apply(
        lambda x: abs((x - x.round(freq="H")).total_seconds())
    )
    # create a new column, named "timestamp_hour_plus_minus", where any
    # timestamp "mins_from_the_hour" (minutes) before or after the hour is given
    # the timestamp of the rounded hour. Times outside this range are assigned None.
    env_data["timestamp_hour_plus_minus"] = env_data.apply(
        lambda x: x["timestamp"].round(freq="H")
        if x["timedelta_in_secs"]
        <= constants["mins_from_the_hour"] * constants["secs_per_min"]
        else None,
        axis=1,
    )
    # remove row entries that have been assigned None above
    env_data = env_data.dropna(subset="timestamp_hour_plus_minus")

    time_vector = timeVector(
        start=min(env_data["timestamp_hour_floor"]),
        end=max(env_data["timestamp_hour_floor"]),
    )

    hour_averages = hourly_average_sensor(
        env_data,
        ["temperature", "humidity"],
        time_vector,
    )

    return env_data, hour_averages
