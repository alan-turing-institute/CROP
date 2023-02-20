from .config import config
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

constants = config(section="constants")
processing_params = config(section="data")
sensors_list = config(section="sensors")
sensors_list = sensors_list["include_sensors"]


def get_time_vector(start, end, frequency="1H", offset=1):
    """
    Create a vector of increasing timestamps.

    Parameters:
        start: starting timestamp.
        end: end timestamp.
        frequency: delta between successive timestamps.
            The default is "1H".
        offset: date offset added to the starting timestamp,
            in hours. The default is 1, as this is what was
            done in the original ARIMA R code.
    Returns:
        time_vector: a pandas dataframe, with a single column
            named "timestamp", containing the vector of increasing
            timestamps.
    """
    if offset != 1:
        logger.warning(
            "!!! The date offset added to the starting timestamp has been set to something different than 1 (hour) !!!"
        )
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


def centered_ma(series: pd.Series, window: int = 3):
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
        logger.error("The moving average window must be an odd integer.")
        raise Exception
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


def clean_env_data(env_data: pd.DataFrame):
    """
    Clean the pandas dataframe containing the temperature and humidity data
    retrieved from the database (DB).

    Parameters:
        env_data: pandas dataframe containing temperature and humidity data
            returned by data_access.get_training_data.
    Returns:
        env_data: a dictionary with keys named after the user-requested sensors.
            The corresponding values are pandas dataframes containing processed
            temperature and humidity data for each sensor (the data is averaged
            based on its timestamp).
        time_vector: a pandas dataframe with a single column named "timestamp",
            containing a vector of increasing timestamps, ranging between the
            oldest and most recent timestamps in the input dataframe, with a
            deltatime between successive timestamps of one hour.
    """
    logger.info("Cleaning temperature/rel humidity data...")
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
        <= processing_params["mins_from_the_hour"] * constants["secs_per_min"]
        else None,
        axis=1,
    )
    # remove row entries that have been assigned None above
    env_data = env_data.dropna(subset="timestamp_hour_plus_minus")
    # create the time vector for which hourly-averaged data will be returned
    time_vector = get_time_vector(
        start=min(env_data["timestamp_hour_floor"]),
        end=max(env_data["timestamp_hour_floor"]),
        frequency=processing_params["time_delta"],
    )
    # calculate the hourly-averaged data
    env_data = hourly_average_sensor(
        env_data,
        ["temperature", "humidity"],
        time_vector,
    )
    logger.info("Done cleaning temperature/rel humidity data.")
    return env_data, time_vector


def clean_energy_data(energy_data: pd.DataFrame):
    """
    Clean the pandas dataframe containing the energy data retrieved from
    the database (DB).

    Parameters:
        energy_data: pandas dataframe containing the energy data returned
            by data_access.get_training_data.
    Returns:
        energy_data: pandas dataframe storing the processed energy data.
            It contains the energy consumption for each sensor, averaged
            as a function of the timestamp. It also contains moving-averaged
            (MA) data.
    """
    logger.info("Cleaning energy data...")
    # pivot the input dataframe, setting the timestamp as the index,
    # sensor_id as columns and electricity_consumption as the values
    # of the new dataframe.
    energy_data = energy_data.pivot(
        index="timestamp", columns="sensor_id", values="electricity_consumption"
    )
    energy_data.columns.name = ""  # remove 'sensor_id' as columns name
    # rename the sensor_id columns as "EnergyCC" and "EnergyCP"
    energy_data.rename(
        columns={16: "EnergyCC", 17: "EnergyCP"},
        inplace=True,
    )
    # convert the timestamp index into a column
    energy_data = energy_data.reset_index(level=0)
    # compute weighted, centered moving averages (MA) using the default window
    # size of 3. The deltatime between successive observations is 30 mins.
    # Therefore, for timestamp t, the average will be computed using the
    # values as t-30min, t and t+30min, with t weighted higher than
    # t-30min and t+30min
    energy_data["EnergyCC_MA"] = centered_ma(
        energy_data.EnergyCC, window=processing_params["window"]
    )
    energy_data["EnergyCP_MA"] = centered_ma(
        energy_data.EnergyCP, window=processing_params["window"]
    )
    # insert a new column at the end of the dataframe, named "timestamp_hour_floor",
    # that rounds the timestamp by flooring to hour precision
    energy_data.insert(
        len(energy_data.columns),
        "timestamp_hour_floor",
        energy_data.timestamp.dt.floor("h"),
    )
    # group the data by "timestamp_hour_floor" and apply the following
    # function to compute the mean or take the first row entry (because it
    # corresponds to the MA for the full hour for time-ordered data).
    def f(x):
        d = {}
        d["EnergyCC"] = x["EnergyCC"].mean()
        d["EnergyCP"] = x["EnergyCP"].mean()
        d["EnergyCC_MA"] = x["EnergyCC_MA"].iloc[0]
        d["EnergyCP_MA"] = x["EnergyCP_MA"].iloc[0]
        return pd.Series(
            d, index=["EnergyCC", "EnergyCP", "EnergyCC_MA", "EnergyCP_MA"]
        )

    # now perform the groupby operation
    energy_data = energy_data.groupby(
        "timestamp_hour_floor",
        as_index=False,
    ).apply(f)
    # rename the "timestamp_hour_floor" column to "timestamp"
    energy_data.rename(
        columns={"timestamp_hour_floor": "timestamp"},
        inplace=True,
    )
    logger.info("Done cleaning energy data.")
    return energy_data


def clean_data(env_data, energy_data):
    """
    Parent function of this module: clean environment (temperature
    and humidity) and energy data retrieved from the database (DB).

    Parameters:
        env_data: pandas dataframe containing temperature and humidity data
            returned by data_access.get_training_data.
        energy_data: pandas dataframe containing the energy data returned
            by data_access.get_training_data.
    Returns:
        env_data: a dictionary with keys named after the user-requested sensors.
            Use the "include_sensors" parameter in "config.ini" to specify the
            sensors. The corresponding values for the dict keys are pandas dataframes
            containing processed temperature and humidity data for each sensor
            (the observations are averaged based on the proximity of the timestamp
            to the full hour - use the "mins_from_the_hour" parameter in "config.ini"
            to specify what timestamps to average together). The processed data is
            time-ordered. The dataframes are indexed by timestamp.
        energy_data: a pandas dataframe containing processed electricity consumption
            for each sensor. "EnergyCC" refers to electricity consumption at Clapham
            Common, and EnergyCP refers to electricity consumption at Carpenter's Place.
            Based on the timestamp of the observations, standard averages and centered
            moving averages are returned (the latter have the subscript "_MA").
            The data is time-ordered. Only timestamps contained in the processed
            "env_data" are returned. The dataframe is indexed by timestamp.
    """
    if processing_params["mins_from_the_hour"] != 15:
        logger.warning(
            "The 'mins_from_the_hour' setting in config.ini has been set to something different than 15."
        )
    if processing_params["time_delta"] != "1H":
        logger.warning(
            "The 'time_delta' setting in config.ini has been set to something different than '1H'."
        )
    if processing_params["window"] != 3:
        logger.warning(
            "The 'window' setting in config.ini has been set to something different than 3."
        )
    env_data, time_vector = clean_env_data(env_data)
    energy_data = clean_energy_data(energy_data)
    # perform a left merge of "energy_data" with "time_vector",
    # so that only timestamps contained in "time_vector" are
    # retained
    energy_data = pd.merge(
        time_vector,
        energy_data,
        how="left",
    )
    # set the timestamp column of the dataframes to index
    keys = list(env_data.keys())
    for key in keys:
        env_data[key].set_index("timestamp", inplace=True)
    energy_data.set_index("timestamp", inplace=True)

    return env_data, energy_data
