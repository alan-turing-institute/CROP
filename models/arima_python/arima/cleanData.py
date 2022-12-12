from .dataAccess import getTrainingData
from .config import config
import pandas as pd

constants = config(section="constants")
sensors_list = config(section="sensors")
sensors_list = sensors_list["include_sensors"]


def timeVector(start, end, frequency="1H", offset=1):
    # create a Pandas fixed frequency DatetimeIndex
    time_vector = pd.date_range(
        start + pd.DateOffset(hours=offset),
        end,
        freq=frequency,
    )
    return time_vector


def hourly_average_sensor(env_data, var_names):
    hour_averages = dict.fromkeys(
        sensors_list
    )  # creates empty dict with specified keys
    keys = list(hour_averages.keys())
    grouped = env_data.groupby("name")  # group by sensor name
    for ii in range(len(hour_averages)):
        sensor = grouped.get_group(keys[ii])
        hour_averages[keys[ii]] = sensor.groupby(
            "timestamp_hour_plus_minus", as_index=False
        )[var_names].mean()
    return hour_averages


def cleanEnvData(env_data):
    # insert a new column at the end of the dataframe, named "hour_truncated",
    # that takes the truncated hour from the "timestamp" column
    env_data.insert(
        len(env_data.columns),
        "hour_truncated",
        env_data.timestamp.dt.hour,
    )
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

    hour_averages = hourly_average_sensor(env_data, ["temperature", "humidity"])

    time_vector = timeVector(
        start=min(env_data["timestamp_hour_floor"]),
        end=max(env_data["timestamp_hour_floor"]),
    )
    return env_data, hour_averages
