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

def remove_time_zone(dataframe: pd.DataFrame):
    """
    Remove timezone information from datetime columns.
    Note that all timestamps in the SQL database should be UTC.

    Parameters:
        dataframe: pandas DataFrame
    """
    new_dataframe = dataframe.select_dtypes("datetimetz")
    if not new_dataframe.empty:
        colnames = new_dataframe.columns.to_list()
        for column in colnames:
            dataframe[column] = pd.to_datetime(dataframe[column]).dt.tz_localize(None)
            
def get_temperature_humidity_data(delta_days, num_rows=None, session=None):
    """Fetch temperature and humidity data from the aranet_trh_data table
    over the specified time period, limited by the specified number of rows.

     Args:
        delta_days (int, optional): Number of days in the past from which to retrieve data. Defaults to 100.
        num_rows (int, optional): Number of rows to limit the data to. 
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
        session.query(
            SensorClass.id,
            SensorClass.name,
            ReadingsAranetTRHClass.id,
            ReadingsAranetTRHClass.sensor_id,
            ReadingsAranetTRHClass.timestamp,
            ReadingsAranetTRHClass.temperature,
            ReadingsAranetTRHClass.humidity,
            ReadingsAranetTRHClass.time_created,
            ReadingsAranetTRHClass.time_updated
        )
        .join(SensorClass, SensorClass.id == ReadingsAranetTRHClass.sensor_id)
        .filter(ReadingsAranetTRHClass.timestamp > data_from)
        .order_by(asc(ReadingsAranetTRHClass.timestamp))
        .limit(num_rows)
    )
    data = (pd
            .read_sql(query.statement, query.session.bind)
            .drop(columns=["id"])
            .rename(columns={"id_1": "id"})
    )
    remove_time_zone(data)
    
    logger.info("Temperature and humidity data - head/tail:")
    logger.info(data.head(5))
    logger.info(data.tail(5))
    
    session_close(session)
    return data

            
def get_energy_data(delta_days, num_rows=None, session=None):
    """ Fetch energy data from the utc_energy_data table
    over the specified time period, limited by the specified
    number of rows.

    Args:
        delta_days (int, optional): Number of days in the past from which to retrieve data. Defaults to 100.
        num_rows (int, optional): Number of rows to limit the data to.
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
    # data['timestamp'] = pd.to_datetime(
    #     data['timestamp'], 
    #     format='%Y-%m-%d %H:%M:%S', 
    #     utc=True
    #     ).dt.tz_localize(None)
    remove_time_zone(data)
    logger.info("Energy data - head/tail:")
    logger.info(data.head(5))
    logger.info(data.tail(5))
    
    session_close(session)
    return data

#df = get_energy_data(100, 20)
df2 = get_temperature_humidity_data(100, 20)
# check data types
print(df2.head(5))
print(df2.dtypes)

# params = config(section="data")
# print(params)
# num_days_training = params["num_days_training"]
# if num_days_training != 200:
#         logger.warning(
#             "The 'num_days_training' setting in config.ini has been set to something different than 200."
#         )