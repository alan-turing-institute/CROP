import arima.arima_utils as arima_utils

# from models.ges.ges.ges_utils import get_sqlalchemy_session
from arima.data_access import (
    data_config,
    get_energy_data,
    get_temperature_humidity_data,
    get_training_data,
)
import pytest


def test_connection():
    """
    Test PostgreSQL connection
    """
    conn = arima_utils.get_sqlalchemy_session()
    assert conn is not None
    arima_utils.session_close(conn)


def test_get_energy_data():
    """
    Test that the format of the energy data fetched
    from the DB is correct.
    """

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
    """
    Test that the format of the temperature and humidity data fetched
    from the DB is correct.
    """

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


def test_get_training_data():
    """
    Test that the format of the training data fetched
    from the DB is correct.
    The training data is fetched from the "aranet_trh_data"
    and "utc_energy_data" tables.
    """
    # fetch 50 rows of training data
    num_rows = 50
    env_data, energy_data = get_training_data(num_rows=num_rows)
    # check that the dataframes have the correct size
    num_cols = 8
    assert env_data.shape == (num_rows, num_cols)
    num_cols = 6
    assert energy_data.shape == (num_rows, num_cols)


def test_num_days_training():
    """
    Test that a ValueError is raised if the `num_days_training`
    parameter in config.ini is set to a value greater than 365.
    """
    with pytest.raises(ValueError):
        data_config["num_days_training"] = 366
        get_training_data(num_rows=50)
