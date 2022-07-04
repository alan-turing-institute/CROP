"""
Utilities module
"""
import sys
import io
import json
from datetime import datetime, timedelta
import pandas as pd
from flask import send_file
from sqlalchemy import and_, func

from __app__.crop.structure import SensorLocationClass


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
        if "_asdict" in dir(rowproxy):
            rowproxy = rowproxy._asdict()
            # print ("rowproxy: ", rowproxy)#
        else:
            None

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


def download_csv(readings, filename_base="results"):
    """
    Use Pandas to convert array of readings into a csv
    Args:
       readings: a list of records to be written out as csv
       filename (optional): str, name of downloaded file
    Returns:
        send_file: function call to flask send_file, will send csv file to client.
    """
    df = pd.DataFrame(readings)
    output_buffer = io.BytesIO()
    df.to_csv(output_buffer)
    output_buffer.seek(0)
    filename = (
        filename_base + "_" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S") + ".csv"
    )
    return send_file(
        output_buffer, download_name=filename, mimetype="text/csv", as_attachment=True
    )


def filter_latest_sensor_location(db):
    """Return a filter object that excludes all but the latest location for each sensor.

    This should be used to filter a query that involves the SensorLocationClass.

    Args:
        db: A database connection.
    Returns:
        An object that can be given as an argument to sqlalchemy.filter.
    """
    query = (
        db.session.query(
            SensorLocationClass.sensor_id,
            func.max(SensorLocationClass.installation_date).label("installation_date"),
        )
        .group_by(SensorLocationClass.sensor_id)
        .subquery()
    )
    return and_(
        query.c.sensor_id == SensorLocationClass.sensor_id,
        query.c.installation_date == SensorLocationClass.installation_date,
    )
