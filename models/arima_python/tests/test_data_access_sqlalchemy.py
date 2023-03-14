import arima.arima_utils as arima_utils
from arima.data_access_sqlalchemy import get_energy_data, get_temperature_humidity_data

def test_connection():
    """
    Test PostgreSQL connection
    """
    conn = arima_utils.get_sqlalchemy_session()
    assert conn is not None
    arima_utils.session_close(conn)
    
def test_get_energy_data():
    
    energy_data = get_energy_data(delta_days=100, num_rows=20)
    
    # check that column names are the expected ones
    colnames = [
        "timestamp",
        "electricity_consumption",
        "time_created",
        "time_updated",
        "sensor_id",
        "id",
    ]
    assert all(item in colnames for item in energy_data.columns)
    
    # check that the dataframe column datatypes are the expectd ones
    datatypes = {
    "timestamp": "<M8[ns]",  # note no time-zone information
    "electricity_consumption": "float64",
    "time_created": "O",
    "time_updated": "O",
    "sensor_id": "int64",
    "id": "int64",
    }
    assert all(
        [energy_data[item].dtypes == datatypes[item] for item in datatypes.keys()]
    )
    
def test_get_temperature_humidity_data():
    
    env_data = get_temperature_humidity_data(delta_days=100, num_rows=20)
    
    # check that the dataframes have the expected column names
    colnames = [
        "name",
        "id",
        "sensor_id",
        "timestamp",
        "temperature",
        "humidity",
        "time_created",
        "time_updated",
    ]
    assert all(item in colnames for item in env_data.columns)
    
    # check that the dataframe column datatypes are the expectd ones
    datatypes = {
        "name": "O",
        "id": "int64",
        "sensor_id": "int64",
        "timestamp": "<M8[ns]",  # note no time-zone information
        "temperature": "float64",
        "humidity": "float64",
        "time_created": "<M8[ns]",  # note no time-zone information
        "time_updated": "O",
    }
    assert all([env_data[item].dtypes == datatypes[item] for item in datatypes.keys()])