"""
Utilities module
"""

import json
from datetime import datetime

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
                    dict_entry = {**dict_entry, **{column: value.replace(microsecond=0)}}
            else:
                dict_entry = {**dict_entry, **{column: value}}
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

