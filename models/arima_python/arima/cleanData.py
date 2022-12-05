from .dataAccess import getTrainingData
from .config import config

env_data, energy_data = getTrainingData(numRows=50)

constants = config(section="constants")


def cleanEnvData():
    # insert a new column at the end of the dataframe, named "hour_truncated",
    # that takes the truncated hour from the "timestamp" column
    env_data.insert(len(env_data.columns), "hour_truncated", env_data.timestamp.dt.hour)
    # insert a new column at the end of the dataframe, named "hour_decimal",
    # that expresses the time of the "timestamp" column in decimal form
    env_data.insert(
        len(env_data.columns),
        "hour_decimal",
        env_data.timestamp.dt.hour
        + env_data.timestamp.dt.minute / constants["secs_per_min"],
    )
    return env_data
