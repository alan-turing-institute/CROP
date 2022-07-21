"""
Python module to read from the PurpleCrane GrowApp database, and write to CROP database.

There is not quite a 1:1 mapping between the CROP tables/columns and the GrowApp tables/columns.

The philosophy in this module is to perform all the necessary logic to do the transformation in the
get_xyz functions, that then return DataFrames containing exactly the data that we want to put into
the CROP tables.
We can then generalize the functions for writing tables into the CROP database, including the
logic for not adding data that is already there (we use the 'growapp_id' column for this).

"""

import logging
import time
from datetime import datetime, timedelta
import requests
import pandas as pd
from urllib import parse

from sqlalchemy import and_
from sqlalchemy.exc import ProgrammingError
from __app__.crop.db import connect_db, session_open, session_close
from __app__.crop.structure import (
    LocationClass,
    CropTypeClass,
    BatchClass,
    BatchEventClass,
    HarvestClass,
)

from __app__.crop.growapp_structure import (
    LocationClass as GrowAppLocationClass,
    CropClass as GrowAppCropClass,
    BatchClass as GrowAppBatchClass,
    BatchEventClass as GrowAppBatchEventClass,
)

from __app__.crop.utils import query_result_to_array
from __app__.crop.constants import (
    GROWAPP_IP,
    GROWAPP_DB,
    GROWAPP_USER,
    GROWAPP_PASSWORD,
    GROWAPP_SCHEMA,
    SQL_CONNECTION_STRING,
    SQL_DBNAME,
    SQL_ENGINE,
)

from __app__.crop.ingress import log_upload_event


def get_growapp_db_session(return_engine=False):
    """
    Get an SQLAlchemy session on the GrowApp database.

    Parameters
    ==========
    return_engine: bool, if True return the sqlalchmy engine as well as session

    Returns
    =======
    session: SQLAlchemy session object
    engine (optional): SQLAlchemy engine
    """
    conn_string = "%s://%s:%s@%s" % (
        SQL_ENGINE,
        GROWAPP_USER,
        parse.quote(GROWAPP_PASSWORD),
        GROWAPP_IP,
    )
    success, log, engine = connect_db(conn_string, GROWAPP_DB)
    if not success:
        logging.info(log)
        return None
    session = session_open(engine)
    if return_engine:
        return session,engine
    else:
        return session


def get_cropapp_db_session(return_engine=False):
    """
    Get an SQLAlchemy session on the CROP database.

    Parameters
    ==========
    return_engine: bool, if True return the sqlalchmy engine as well as session

    Returns
    =======
    session: SQLAlchemy session object
    engine (optional): SQLAlchemy engine
    """
    success, log, engine = connect_db(SQL_CONNECTION_STRING, SQL_DBNAME)
    if not success:
        logging.info(log)
        return None
    session = session_open(engine)
    if return_engine:
        return session,engine
    else:
        return session


def get_croptype_data():
    """
    Read from the table of crops in the GrowApp database

    Returns
    =======
    crop_df: pandas DataFrame of results
    """
    session = get_growapp_db_session()
    query = session.query(
        GrowAppCropClass.id,
        GrowAppCropClass.name,
        GrowAppCropClass.seed_density,
        GrowAppCropClass.propagation_period,
        GrowAppCropClass.grow_period,
        GrowAppCropClass.is_pre_harvest
    )
    # get the results to an array of dicts before putting into
    # pandas dataframe, to avoid
    # https://github.com/pandas-dev/pandas/issues/40682
    results = session.execute(query).fetchall()
    results_array = query_result_to_array(results)
    crop_df = pd.DataFrame(results_array)
    crop_df.rename(columns={"id":"growapp_id"}, inplace=True)
    crop_df["growapp_id"] = crop_df["growapp_id"].astype(str)
    session_close(session)
    return crop_df


def get_existing_growapp_ids(session, DbClass):
    """
    Read from the table of crops in the CROP database to get list
    of existing growapp_ids.

    Parameters
    ==========
    session: SQLAlchemy session object
    DbClass: class as defined in structure.py.  Assumed to have 'growid' attribute.

    Returns
    =======
    existing_growids: pandas DataFrame
    """
    query = session.query(
        DbClass.growapp_id
    )
    results = session.execute(query).fetchall()
    results_array = query_result_to_array(results)
    existing_growids = pd.DataFrame(results_array)
    if len(existing_growids) > 0:
        existing_growids.set_index("growapp_id", inplace=True)
    return existing_growids


def write_new_data(data_df, DbClass):
    """
    First read from the table in the CROP database to get list
    of existing growapp_ids, then remove those rows from the input data_df,
    and write the remaining ones back to the CROP database.
    Relies on there being a column 'growapp_id' in the table, in order to
    identify existing rows.

    Parameters
    ==========
    crop_df: pandas DataFrame containing data from the GrowApp db.
    DbClass: SQLAlchemy ORM class, corresponding to target table, as defined in structure.py

    Returns
    =======
    success: bool

    """
    session, engine = get_cropapp_db_session(return_engine=True)
    existing_growids = get_existing_growapp_ids(session, CropTypeClass)
    if len(existing_growids) > 0:
        existing_index = existing_growids.index
        data_df = data_df[~data_df["growapp_id"].isin(existing_index)]

    try:
        DbClass.__table__.create(bind=engine)
    except ProgrammingError:
        # The table already exists.
        pass
    logging.info(f"==> Will write {len(data_df)} rows to {DbClass.__tablename__}")
    # loop over all rows in the dataframe
    data_df["growapp_id"] = data_df.index
    for _ , row in data_df.iterrows():
        new_row = DbClass(**(row.to_dict()))
        session.add(new_row)
    logging.info(f"Finished writing to {DbClass.__tablename__}")
    session.commit()
    session_close(session)
