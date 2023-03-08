import arima.arima_utils as arima_utils


def test_connection():
    """
    Test PostgreSQL connection
    """
    conn = arima_utils.get_sqlalchemy_session()
    assert conn is not None
    arima_utils.session_close(conn)