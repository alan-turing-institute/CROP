import os
import argparse
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
from sqlalchemy import and_, desc
from config import config_dict
from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    ReadingsZensieTRHClass,
)
from webapp.crop_app import create_app
from config import config_dict
from utilities.utils import query_result_to_array


def construct_query(sensor_ids, start_date=None, end_date=None):
    """
    Default is to go back 1 year.  If start and end date are provided,
    use them.  If only one is provided, use 1 year before or after it.
    """
    dt_to = datetime.now()
    dt_from = dt_to - relativedelta(years=1)
    if start_date:
        dt_from = datetime.strptime(start_date, "%Y-%m-%d")
        if not end_date:
            dt_to = dt_from + relativedelta(years=1)
    if end_date:
        dt_to = datetime.strptime(end_date, "%Y-%m-%d")
        if not start_date:
            dt_from = dt_to - relativedelta(years=1)
    query = (
        db.session.query(
            ReadingsZensieTRHClass.timestamp,
            ReadingsZensieTRHClass.temperature,
            ReadingsZensieTRHClass.humidity,
            ReadingsZensieTRHClass.time_created,
            ReadingsZensieTRHClass.time_updated,
            ReadingsZensieTRHClass.sensor_id,
        )
        .filter(
            and_(
                ReadingsZensieTRHClass.timestamp >= dt_from,
                ReadingsZensieTRHClass.timestamp <= dt_to,
            )
        )
        .filter(ReadingsZensieTRHClass.sensor_id.in_(sensor_ids))
        .order_by(desc(ReadingsZensieTRHClass.timestamp))
    )
    return query


def get_full_dataframe(query):
    readings = db.session.execute(query).fetchall()
    df_all = pd.DataFrame(readings)
    return df_all


def get_pivoted_dataframe(df, columns):
    df_pivot = df.pivot(index="timestamp", columns="sensor_id", values=columns)
    df_pivot.columns = [f"{i}_{j}" for i, j in df_pivot.columns]
    return df_pivot


def write_csv(df, csv_filename):
    df.to_csv(csv_filename)


def main(args):
    start_date = args.start_date if args.start_date else None
    end_date = args.end_date if args.end_date else None
    query = construct_query(args.sensor_ids, start_date, end_date)
    df_all = get_full_dataframe(query)
    columns = ["temperature", "humidity"]
    df = get_pivoted_dataframe(df_all, columns)
    write_csv(df, args.output_csv)


if __name__ == "__main__":
    config_mode = config_dict["Production"]
    app = create_app(config_mode)
    app.app_context().push()

    parser = argparse.ArgumentParser(description="download a csv of readings from db")
    parser.add_argument(
        "--sensor_ids",
        type=int,
        nargs="+",
        help="space-separated list of integer sensor_ids",
    )
    parser.add_argument(
        "--output_csv",
        type=str,
        help="name of output csv file - will have temperature_ or humidity_ prepended to it",
        default="ZensieTRH.csv",
    )
    parser.add_argument("--start_date", type=str, help="time in format YYYY-MM-DD")
    parser.add_argument("--end_date", type=str, help="time in format YYYY-MM-DD")
    args = parser.parse_args()
    main(args)
