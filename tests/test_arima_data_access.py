from models.arima_python.arima.config import config
from cropcore.db import connect_db, session_open, session_close
from cropcore.model_data_access import get_training_data, get_sqlalchemy_session
import pytest
import warnings


def test_connection():
    """
    Test PostgreSQL connection
    """
    conn = get_sqlalchemy_session()
    assert conn is not None
    session_close(conn)


def test_get_training_data():
    """
    Test that the format of the training data fetched
    from the DB is correct.
    The training data is fetched from the "aranet_trh_data"
    and "utc_energy_data" tables.
    """
    # fetch 50 rows of training data
    num_rows = 50
    env_data, energy_data = get_training_data(
        num_rows=num_rows,
        config_sections=["env_data", "energy_data"],
        arima_config=config,
    )
    # check that the dataframes have the correct size
    num_cols = 8
    assert env_data.shape == (num_rows, num_cols)
    num_cols = 6
    if len(energy_data) > 0:
        assert (
            energy_data.shape[-1] == num_cols
        )  # num_rows not checked in case energy table empty

    # check that energy table column names are the expected ones
    colnames = [
        "timestamp",
        "electricity_consumption",
        "time_created",
        "time_updated",
        "sensor_id",
        "id",
    ]
    assert all(item in colnames for item in energy_data.columns)

    # check that the energy table datatypes are the expectd ones
    datatypes = {
        "timestamp": "<M8[ns]",  # note no time-zone information
        "electricity_consumption": "float64",
        "time_created": "O",
        "time_updated": "O",
        "sensor_id": "int64",
        "id": "int64",
    }
    if not energy_data.empty:
        assert all(
            [energy_data[item].dtypes == datatypes[item] for item in datatypes.keys()]
        )
    else:
        warnings.warn("The energy data table is empty.")

    # check that temperature/humidity table column names are the expected ones
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

    # check that the temperature/humidity table datatypes are the expectd ones
    datatypes = {
        "name": "O",
        "id": "int64",
        "sensor_id": "int64",
        "timestamp": "<M8[ns]",  # note no time-zone information
        "temperature": "float64",
        "humidity": "float64",
        "time_created": "O",  # note no time-zone information
        "time_updated": "O",
    }
    assert all([env_data[item].dtypes == datatypes[item] for item in datatypes.keys()])


def test_num_days_training():
    """
    Test that a ValueError is raised if the number of days
    into the past for which to retrieve training data is
    greater than 365.
    """
    with pytest.raises(ValueError):
        get_training_data(delta_days=366, num_rows=50, arima_config=config)
