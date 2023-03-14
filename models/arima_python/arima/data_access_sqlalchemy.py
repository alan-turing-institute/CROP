import logging
import datetime
import pandas as pd

from .config import config
from sqlalchemy import desc, asc, exc, func

from cropcore.db import connect_db, session_open, session_close
from cropcore.structure import (
    SensorClass,
    ReadingsAranetTRHClass,
    ReadingsEnergyClass
)
    
from .arima_utils import get_sqlalchemy_session

logger = logging.getLogger(__name__)


def get_energy_data(delta_days=100, num_rows=20, session=None):
    """ Fetch energy data from the utc_energy_data table
    over the specified time period, limited by the specified
    number of rows.

    Args:
        delta_days (int, optional): Number of days in the past from which to retrieve data. Defaults to 100.
        num_rows (int, optional): Number of rows to limit the data to. Defaults to 20.
        session (_type_, optional): _description_. Defaults to None.

    Returns:
        data: A pandas dataframe with each row corresponding to a different row of the DB table, 
        sorted by the timestamp column of the utc_energy_data table.
    """
    if not session:
        session = get_sqlalchemy_session()
    date_to = datetime.datetime.now()
    delta = datetime.timedelta(days=delta_days)
    data_from = date_to - delta
    query = (
        # retrieve all columns from the ReadingsEnergyClass table
        session.query(
            ReadingsEnergyClass.timestamp,
            ReadingsEnergyClass.electricity_consumption,
            ReadingsEnergyClass.time_created,
            ReadingsEnergyClass.time_updated,
            ReadingsEnergyClass.sensor_id,
            ReadingsEnergyClass.id
            )
        .filter(ReadingsEnergyClass.timestamp > data_from)
        .order_by(asc(ReadingsEnergyClass.timestamp))
        .limit(num_rows)
    )
    data = pd.read_sql(query.statement, query.session.bind)
    # convert timestamp column to datetime and remove timezone
    data['timestamp'] = pd.to_datetime(
        data['timestamp'], 
        format='%Y-%m-%d %H:%M:%S', 
        utc=True
        ).dt.tz_localize(None)
    
    logger.info("Energy data - head/tail:")
    logger.info(data.head(5))
    logger.info(data.tail(5))
    
    session_close(session)
    return data

df = get_energy_data()

# check data types
print(df.dtypes)