from .config import config
from datetime import datetime, timedelta

constants = config(section="constants")
data_config = config(section="data")
arima_config = config(section="arima")


def standardize_timestamp(timestamp):
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
