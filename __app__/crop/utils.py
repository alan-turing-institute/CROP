"""
Utilities (miscellaneous routines) module

"""
from datetime import datetime


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


def query_result_to_array(query_result, date_iso=True):
    """
    Forms an array of ResultProxy results.

    Args:
        query_result: a ResultProxy representing results of the sql alchemy query execution
    Returns:
        results_arr: an array with ResultProxy results
    """

    dict_entry, results_arr = {}, []
    for rowproxy in query_result:

        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():

            if isinstance(value, datetime):
                if date_iso:
                    dict_entry = {**dict_entry, **{column: value.isoformat()}}
                else:
                    dict_entry = {
                        **dict_entry,
                        **{column: value.replace(microsecond=0)},
                    }
            else:
                dict_entry = {**dict_entry, **{column: value}}
        results_arr.append(dict_entry)

    return results_arr
