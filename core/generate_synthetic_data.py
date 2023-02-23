"""
For sensor readings:
   Generate a set of points at specified frequency,
   based on sum of one or more sinusoidal functions,
   with Gaussian noise.
For crop data:
   Select from subset of crop types, and generate random
   crops in shelves at random times.
"""

from datetime import datetime, timedelta
import random
import pandas as pd
import numpy as np

CROP_TYPES = [
        "peashoots",
        "peashoots",
        "purple radish",
        "garlic chive",
        "garlic chive",
        "red_cabbage",
        None
]

def generate_timepoints(start_time, end_time, interval):
    """
    generate a numpy array of unix timestamps, with specified start_time,
    end_time and interval

    Parameters
    ==========
    start_time, end_time: datetime
    interval: int, time in seconds

    Returns
    =======
    np.array - evenly spaced array of timestamps
    """
    start_time = int(start_time.timestamp())
    end_time = int(end_time.timestamp())
    num_steps = int((end_time - start_time) // interval)
    end_time = start_time + num_steps * interval
    return np.linspace(start_time, end_time, num_steps)


def initial_dataframe(start_time, end_time, interval, colnames=["values"]):
    """
    generate a numpy array of unix timestamps, with specified start_time,
    end_time and interval

    Parameters
    ==========
    start_time, end_time: datetime
    interval: int, time in seconds
    colnames: list of strings, starting list of column names

    Returns
    =======
    df: pandas DataFrame with one row per timestamp, timestamps in Unix format
    """
    timestamps = generate_timepoints(start_time, end_time, interval)

    init_values = np.zeros(len(timestamps))
    df = pd.DataFrame(
        {"timestamp": timestamps, **{k: np.zeros(len(timestamps)) for k in colnames}}
    )
    return df


def add_const_offset(df, colname, value):
    """
    Add a constant offset to all of the values in the dataframe

    Parameters
    ==========
    df: pandas DataFrame
    colname: str, name of column to be modified
    value: float value of offset
    """
    df[colname] = df[colname] + value
    return df


def add_sinusoid(df, colname, amplitude, period, offset=0):
    """
    Add a sinusoidal oscillation to a specified column

    Parameters
    ==========
    df: pandas.DataFrame containing one or more measurement columns
    colname: str, name of column to modify values of
    amplitude: float, amplitude of sinusoidal oscillation
    period: float, period of oscillation, in seconds
    offset: float, phase of oscillation, in seconds

    Returns
    =======
    df: pandas.DataFrame, same format as input
    """
    start_time = df.timestamp.values[0]
    offsets = df.timestamp.values - df.timestamp.values[0]
    values = amplitude * np.sin(2 * np.pi * (offsets + offset) / period)
    df[colname] += values
    return df


def add_gaussian_noise(df, colname, mean, std):
    """
    Add Gaussian offset to each value of a specified column in the dataframe
    """
    offsets = np.random.normal(mean, std, len(df.index))
    df[colname] = df[colname] + offsets
    return df


def convert_timestamp_column(df):
    """
    Convert from unix timestamp back to a datetime
    """
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    return df


def add_integer_column(df, colname, minval, maxval):
    """
    Add a new integer column with values between minval and maxval
    """
    values = np.random.randint(minval, maxval, len(df.index))
    df[colname] = values
    return df


def add_string_column(df, colname, options=[], basename=""):
    """
    Add a new string column with either random integers appended to basename,
    or a random choice.
    """
    if options:
        values = np.random.choice(options, len(df.index))
    else:
        values = []
        for _ in range(len(df.index)):
            values.append(basename + str(random.randint(1, 9)))
        values = np.array(values)
    df[colname] = values


def generate_trh_readings(sensor_ids=list(range(1, 9))):
    """
    Generate a pandas dataframe for each sensor id, then
    concatenate them at the end.
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=100)
    sampling_period = 600  # 10 mins
    dfs = []
    for sensor_id in sensor_ids:
        df = initial_dataframe(
            start_time, end_time, sampling_period, colnames=["temperature", "humidity"]
        )
        #### Temperature
        df = add_const_offset(df, "temperature", 18.0)
        # daily oscillation
        df = add_sinusoid(df, "temperature", 3.0, 60 * 60 * 24)
        # yearly oscillation
        df = add_sinusoid(df, "temperature", 4.0, 60 * 60 * 24 * 365)
        # random noise
        df = add_gaussian_noise(df, "temperature", 0.0, 0.5)
        ### Humidity
        df = add_const_offset(df, "humidity", 50.0)
        df = add_sinusoid(df, "humidity", 10.0, 60 * 60 * 24)
        df = add_sinusoid(df, "humidity", 10.0, 60 * 60 * 24 * 365)
        df = add_gaussian_noise(df, "humidity", 0.0, 3.0)
        df = convert_timestamp_column(df)
        df["sensor_id"] = sensor_id
        dfs.append(df)
    df = pd.concat(dfs)
    return df


def generate_co2_readings(sensor_ids=list(range(9, 10))):
    """
    Generate a pandas dataframe for each sensor id, then
    concatenate them at the end.
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=100)
    sampling_period = 600  # 10 mins
    dfs = []
    for sensor_id in sensor_ids:
        df = initial_dataframe(start_time, end_time, sampling_period, colnames=["co2"])
        df = add_const_offset(df, "co2", 200.0)
        # daily oscillation
        df = add_sinusoid(df, "co2", 30.0, 60 * 60 * 24)
        # yearly oscillation
        df = add_sinusoid(df, "co2", 40.0, 60 * 60 * 24 * 365)
        # random noise
        df = add_gaussian_noise(df, "co2", 0.0, 10.0)
        df = convert_timestamp_column(df)
        df["sensor_id"] = sensor_id
        dfs.append(df)
    df = pd.concat(dfs)
    return df


def generate_airvelocity_readings(sensor_ids=list(range(11, 15))):
    """
    Generate a pandas dataframe for each sensor id, then
    concatenate them at the end.
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=100)
    sampling_period = 600  # 10 mins
    dfs = []
    for sensor_id in sensor_ids:
        df = initial_dataframe(
            start_time, end_time, sampling_period, colnames=["air_velocity"]
        )
        df = add_const_offset(df, "air_velocity", 200.0)
        # daily oscillation
        df = add_sinusoid(df, "air_velocity", 30.0, 60 * 60 * 24)
        # yearly oscillation
        df = add_sinusoid(df, "air_velocity", 40.0, 60 * 60 * 24 * 365)
        # random noise
        df = add_gaussian_noise(df, "air_velocity", 0.0, 10.0)
        df = convert_timestamp_column(df)
        df["sensor_id"] = sensor_id
        dfs.append(df)
    df = pd.concat(dfs)
    return df


def generate_weather(start_time=None, end_time=None):
    """
    Generate hourly weather history or forecasts going back/forward 10 days.
    For now, just include temperature and humidity.

    Parameters
    ==========
    start_time, end_time: datetime.datetime.
                If None, do weather history for past 10 days.
                Can also set times to do weather forecast
    """
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(days=10)
    sampling_period = 3600  # 1 hour
    df = initial_dataframe(
        start_time,
        end_time,
        sampling_period,
        colnames=["temperature", "relative_humidity"],
    )
    df = add_const_offset(df, "temperature", 10.0)
    df = add_const_offset(df, "relative_humidity", 50.0)
    # daily oscillation
    df = add_sinusoid(df, "temperature", 5.0, 60 * 60 * 24)
    df = add_sinusoid(df, "relative_humidity", -10, 60 * 60 * 24)
    # yearly oscillation for temperature
    df = add_sinusoid(df, "temperature", 10.0, 60 * 60 * 24 * 365)
    # random noise
    df = add_gaussian_noise(df, "temperature", 0.0, 2.0)
    df = add_gaussian_noise(df, "relative_humidity", 0.0, 5.0)
    df = convert_timestamp_column(df)
    # round times to nearest hour
    df["timestamp"] = df["timestamp"].round("60min")
    df["sensor_id"] = 15  # don't think this matters, but column is non-nullable
    return df


def generate_weather_forecast():
    """
    Generate hourly weather forecasts going forward 10 days.
    For now, just include temperature and humidity.
    """
    start_time = datetime.now()
    end_time = start_time + timedelta(days=10)
    df = generate_weather(start_time, end_time)
    return df


def generate_batches_in_farm():
    """
    Generate synthetic data about batches on each shelf in the farm.
    """

    TUNNEL_AISLES_DICT = {
        "Tunnel3": ["A", "B"],
        "Tunnel4": ["E"],
        "Tunnel5": ["C"],
        "Tunnel6": ["D"],
    }
    AISLES_COLUMNS_DICT = {"A": 32, "B": 32, "C": 24, "D": 16, "E": 12}
    NUM_SHELVES = 4
    all_shelf_data = []
    for tunnel, aisles in TUNNEL_AISLES_DICT.items():
        for aisle in aisles:
            for column in range(1, AISLES_COLUMNS_DICT[aisle] + 1):
                for shelf in range(1, NUM_SHELVES + 1):
                    crop = random.choice(CROP_TYPES)
                    n_trays = 8 if tunnel=="Tunnel3" else 10
                    tray_size = 2.4 if tunnel=="Tunnel3" else 3.0
                    # random time in the past week
                    hours_past = timedelta(hours=random.randint(1,24*7))
                    transfer_time = datetime.now() - hours_past
                    transfer_time = transfer_time.replace(
                        minute=0,
                        second=0,
                        microsecond=0
                    )
                    # 8 days after transfer time
                    harvest_time = transfer_time + timedelta(days=8)
                    if not crop:
                        continue
                    shelf_data = {
                        "zone": tunnel,
                        "aisle": aisle,
                        "column": column,
                        "shelf": shelf,
                        "crop_type_name": crop,
                        "number_of_trays": n_trays,
                        "tray_size": tray_size,
                        "event_time": transfer_time.isoformat(),
                        "expected_harvest_time": harvest_time.isoformat()
                    }
                    all_shelf_data.append(shelf_data)
    # reverse the list so that it will go forward in time
    all_shelf_data.reverse()
    return all_shelf_data


def generate_shelf_history():
    """
    Generate some synthetic time sequence of crops/harvests on a shelf
    """
    end_time = datetime.now() - timedelta(days=8)
    num_steps = random.randint(2,5)
    history_entries = []
    # step back in time from the current end_time
    for _ in range(num_steps):
        crop_type = random.choice(CROP_TYPES)
        start_time = end_time - timedelta(days=random.randint(5,8))
        unit_yield = float(random.randint(700,3500))
        waste_disease = 0
        waste_defect = 0
        # some small chance of disease or defect (5% chance each)
        r = random.random()
        if r < 0.05:
            # if there is disease, let it affect between 50 and 100% of crop
            waste_disease = random.randint(5,10) * 10
        elif r < 0.1:
            # same logic for defect
            waste_defect = random.randint(5,10) * 10
        unit_yield = unit_yield * (1 - (waste_defect+waste_disease)/100.)
        # only add an entry to our output if crop_type is not None
        if crop_type:
            entry = {
                "transfer_time": start_time.replace(minute=0,
                                                    second=0,
                                                    microsecond=0).isoformat(),
                "harvest_time": end_time.replace(minute=0,
                                                 second=0,
                                                 microsecond=0).isoformat(),
                "unit_yield": unit_yield,
                "waste_disease": waste_disease,
                "waste_defect": waste_defect,
                "crop_type": crop_type
            }
            history_entries.append(entry)
        # end of previous time window is start of this one
        end_time = start_time
    return history_entries
