from .config import config
from datetime import datetime, timedelta

constants = config(section="constants")
data_config = config(section="data")
arima_config = config(section="arima")


def standardize_latest_timestamp(latest_timestamp):
    farm_cycle_start = arima_config[
        "farm_cycle_start"
    ]  # hour at which the farm cycle starts
    farm_cycle_start = datetime.strptime(farm_cycle_start, "%Hh%Mm%Ss")
    farm_cycle_start = datetime.combine(
        latest_timestamp.date(), farm_cycle_start.time()
    )

    if latest_timestamp >= farm_cycle_start:
        latest_timestamp = farm_cycle_start
    elif latest_timestamp <= (
        farm_cycle_start - timedelta(hours=constants["hrs_per_day"] / 2)
    ):
        latest_timestamp = datetime.combine(
            (latest_timestamp - timedelta(days=1)).date(),
            farm_cycle_start.time(),
        )
    else:
        latest_timestamp = farm_cycle_start - timedelta(
            hours=constants["hrs_per_day"] / 2
        )
    return latest_timestamp
