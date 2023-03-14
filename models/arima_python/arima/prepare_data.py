from .config import config
from datetime import datetime, timedelta

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


def prepare_data(env_clean, energy_clean):
    # obtain the standardized timestamp.
    # note that both `env_clean` and `energy_clean` are indexed by the same timestamps.
    timestamp_standardized = standardize_timestamp(energy_clean.index[-1])
    # keep only the observations whose timestamp is smaller or equal to the
    # standardized timestamp
    keys = list(env_clean.keys())
    for key in keys:
        env_clean[key].drop(
            env_clean[key][env_clean[key].index > timestamp_standardized].index,
            inplace=True,
        )
    energy_clean.drop(
        energy_clean[energy_clean.index > timestamp_standardized].index,
        inplace=True,
    )
    # compute the total hourly energy consumption, given the sampling frequency
    # of the `utc_energy_data` table
    freq_energy_data = data_config["freq_energy_data"]
    freq_energy_data = datetime.strptime(freq_energy_data, "%Hh%Mm%Ss")
