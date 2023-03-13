from .config import config
from datetime import datetime, timedelta

constants = config(section="constants")
data_config = config(section="data")
arima_config = config(section="arima")


def standardize_timestamp(timestamp):
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
