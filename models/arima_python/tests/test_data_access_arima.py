import arima.data_access as data_access
import pytest


def test_connection():
    """
    Test PostgreSQL connection
    """
    conn = data_access.open_connection()
    assert conn is not None
    data_access.close_connection(conn)


def test_get_training_data():
    """
    Test that the format of the training data fetched
    from the DB is correct.
    The training data is fetched from the "aranet_trh_data"
    and "utc_energy_data" tables.
    """
    conn = data_access.open_connection()  # open PostgreSQL connection
    # fetch 50 rows of training data
    num_rows = 50
    env_data, energy_data = data_access.get_training_data(num_rows=num_rows)
    data_access.close_connection(conn)  # close PostreSQL connection
    # check that the dataframes have the correct size
    num_cols = 8
    assert env_data.shape == (num_rows, num_cols)
    num_cols = 6
    assert energy_data.shape == (num_rows, num_cols)
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


def test_num_days_training():
    """
    Test that a ValueError is raised if the `num_days_training`
    parameter in config.ini is set to a value greater than 365.
    """
    with pytest.raises(ValueError):
        data_access.data_config["num_days_training"] = 366
        data_access.get_training_data(num_rows=50)
