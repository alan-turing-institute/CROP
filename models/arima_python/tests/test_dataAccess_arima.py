import arima.dataAccess as dataAccess


def test_connection():
    """
    Test PostgreSQL connection
    """
    conn = dataAccess.openConnection()
    assert conn is not None
    dataAccess.closeConnection(conn)


def test_getTrainingData():
    """
    Test that the format of the training data fetched
    from the DB is in the correct format.
    The training data is fetched from the "aranet_trh_data"
    and "utc_energy_data" tables.
    """
    conn = dataAccess.openConnection()  # open PostgreSQL connection
    # fetch 50 rows of training data
    numRows = 50
    env_data, energy_data = dataAccess.getTrainingData(numRows=numRows)
    dataAccess.closeConnection(conn)  # close PostreSQL connection
    # check that the dataframes have the correct size
    numCols = 8
    assert env_data.shape == (numRows, numCols)
    numCols = 6
    assert energy_data.shape == (numRows, numCols)
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
        "timestamp": "<M8[ns]",
        "temperature": "float64",
        "humidity": "float64",
        "time_created": "<M8[ns]",
        "time_updated": "O",
    }
    assert all([env_data[item].dtypes == datatypes[item] for item in datatypes.keys()])
    datatypes = {
        "timestamp": "<M8[ns]",
        "electricity_consumption": "float64",
        "time_created": "O",
        "time_updated": "O",
        "sensor_id": "int64",
        "id": "int64",
    }
    assert all(
        [energy_data[item].dtypes == datatypes[item] for item in datatypes.keys()]
    )
