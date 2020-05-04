"""
Utilities (miscellaneous routines) module

"""

def make_conn_string(sql_engine, sql_user, sql_password, sql_host, sql_port):
    """
    Constructs a connection string.
    Arguments:
        sql_engine
        sql_user
        sql_password
        sql_host
        sql_port

    Returns:
        connection string
    """

    return "%s://%s:%s@%s:%s" % (
        sql_engine,
        sql_user,
        sql_password,
        sql_host,
        sql_port,
    )