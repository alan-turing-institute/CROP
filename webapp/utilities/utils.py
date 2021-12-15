"""
Utilities module
"""

import json
from datetime import datetime, timedelta


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

        # NOTE: added  ._asdict() as rowproxy didnt come in the form of dict and could not read .items.
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        if '_as_dict' in dir(rowproxy):
            rowproxy=rowproxy._asdict()
            #print ("rowproxy: ", rowproxy)#
        else:  None

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
        #dict_entry["ID"]=21
        results_arr.append(dict_entry)

    return results_arr


def jasonify_query_result(query_result):
    """
    Jasonifies ResultProxy results.

    Args:
        query_result: a ResultProxy representing results of the sql alchemy query execution
    Returns:
        result: jasonified result of the query_result
    """

    results_arr = query_result_to_array(query_result)

    result = json.dumps(results_arr, ensure_ascii=True, indent=4, sort_keys=True)

    return result


def get_default_datetime_range():
    """
    Returns a default datetime range (7 days): dt_from, dt_to
    """

    time_delta = -7

    dt_to = (
        datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        + timedelta(days=1)
        + timedelta(milliseconds=-1)
    )

    dt_from = (dt_to + timedelta(time_delta)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    return dt_from, dt_to


def parse_date_range_argument(request_args):
    """
    Parses date range arguments from the request_arguments string.

    Arguments:
        request_args - request arguments as a string
        arg - argument to be extracted from the request arguments

    Returns parsed argument
    """

    if request_args is None:
        return get_default_datetime_range()

    try:
        dt_to = (
            datetime.strptime(request_args.split("-")[1], "%Y%m%d").replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            + timedelta(days=1)
            + timedelta(milliseconds=-1)
        )

        dt_from = datetime.strptime(request_args.split("-")[0], "%Y%m%d").replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        return dt_from, dt_to

    except ValueError:
        return get_default_datetime_range()
