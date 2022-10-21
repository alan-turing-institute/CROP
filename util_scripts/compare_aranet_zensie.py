# This script was used to check consistency when transitioning from using the Zensie
# 30MHz API to the Hyper API. Once the transition is complete, this script can be
# removed.

# make plots of temperature or humidity data over a specified date
# range for a specified sensor
#
# usage:
#    python compare_aranet_zensie.py --sensor_id <sensor_id> --variable <"temperature" or "humidity"> --start_date <"YYYY-MM-DDTHH:mm:ss"> --end_date <"YYYY-MM-DDTHH:mm:ss">
#

import argparse
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from __app__.crop.constants import (
    SQL_CONNECTION_STRING,
    SQL_DBNAME,
)
from __app__.crop.structure import (
    ReadingsZensieTRHClass,
    ReadingsAranetTRHClass,
)
from __app__.crop.db import connect_db, session_open, session_close

conn_string = SQL_CONNECTION_STRING
database = SQL_DBNAME
success, log, engine = connect_db(conn_string, database)
from sqlalchemy import and_

session = session_open(engine)

date_to = datetime.utcnow()
date_from = date_to + timedelta(days=-7)


def get_results_df(readings_class, date_from, date_to):
    """
    Query the database using the specified SQLAlchemy class

    Parameters
    ----------
    readings_class: SQLAlchemy class, as defined in structure.py
    date_from: datatime
    date_to: datetime

    Returns
    -------
    pandas DataFrame
    """

    query = session.query(
        readings_class.timestamp,
        readings_class.temperature,
        readings_class.humidity,
        readings_class.sensor_id,
    ).filter(
        and_(
            readings_class.timestamp >= date_from,
            readings_class.timestamp <= date_to,
        )
    )

    results = pd.DataFrame(session.execute(query).fetchall())
    print("Got results {}".format(len(results)))
    results.columns = ["timestamp", "temperature", "humidity", "sensor_id"]
    results.set_index("timestamp", inplace=True)
    return results


def plot_results(df, variable, sensor_id, axes=None):
    """
    Given a dataframe, plot temperature or humidity for a chosen sensor
    as a line plot on a given set of axes.

    Parameters
    ----------
    df: pandas DataFrame
    variable: "temperature" or "humidity"
    sensor_id: int, integer primary key from Sensors table in CROP db.
    axes: matplotlib.pylot axes object
    """
    df = df[df.sensor_id == sensor_id]
    p = df[variable].plot(ax=axes)
    return p


def main(args):
    date_from = datetime.strptime(args.start_date, dt_format)
    date_to = datetime.strptime(args.end_date, dt_format)
    sensor_id = args.sensor_id
    variable = args.variable
    print("Getting Zensie data")
    zensie_df = get_results_df(ReadingsZensieTRHClass, date_from, date_to)
    print("Getting Aranet data")
    aranet_df = get_results_df(ReadingsAranetTRHClass, date_from, date_to)
    fig, axes = plt.subplots(1, 2)
    plot_results(aranet_df, variable, sensor_id, axes[0])
    plot_results(zensie_df, variable, sensor_id, axes[1])
    plt.show()


if __name__ == "__main__":
    dt_format = "%Y-%m-%dT%H:%M:%S"
    default_end = datetime.now().strftime(dt_format)
    default_start = (datetime.now() - timedelta(days=7)).strftime(dt_format)
    parser = argparse.ArgumentParser(description="compare data from aranet and zensie")
    parser.add_argument(
        "--start_date",
        type=str,
        default=default_start,
        help="starting date, format YYYY-MM-DDTHH:MM:SS",
    )
    parser.add_argument(
        "--end_date",
        type=str,
        default=default_end,
        help="ending date, format YYYY-MM-DDTHH:MM:SS",
    )
    parser.add_argument("--sensor_id", type=int, help="sensor_id in CROP db")
    parser.add_argument(
        "--variable",
        choices=["temperature", "humidity"],
        help="temperature or humidity",
        default="temperature",
    )
    args = parser.parse_args()
    main(args)
