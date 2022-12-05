from .dataAccess import getTrainingData
from .config import config

env_data, energy_data = getTrainingData(numRows=50)

constants = config(section="constants")


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
    # create a new column, named "timedelta_in_secs", that expresses
    # the time difference, in seconds, between a timestamp and
    # itself rounded to the hour
    env_data["timedelta_in_secs"] = env_data["timestamp"].apply(
        lambda x: abs((x - x.round(freq="H")).total_seconds())
    )
    # create a new column, named "timestamp_plus_minus", where any
    # timestamp 15min before or after the hour is given the timestamp
    # of the rounded hour. Times outside this range are assigned None.
    env_data["timestamp_plus_minus"] = env_data.apply(
        lambda x: x["timestamp"].round(freq="H")
        if x["timedelta_in_secs"] <= 15 * constants["secs_per_min"]
        else None,
        axis=1,
    )
    return env_data
