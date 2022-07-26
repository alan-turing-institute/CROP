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
    ZoneClass as GrowAppZoneClass,
    AisleClass as GrowAppAisleClass,
    StackClass as GrowAppStackClass,
    ShelfClass as GrowAppShelfClass,
    BenchClass as GrowAppBenchClass,
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

BATCH_EVENT_TYPE_MAPPING = {
    0: 0, # none
    10: 1, # weigh
    20: 2, # propagate
    30: 3, # transfer
    40: 4, # harvest
    99: 99, # edit
}


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
        return session, engine
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
        return session, engine
    else:
        return session


def convert_growapp_foreign_key(growapp_df, growapp_column_name, CropDbClass):
    """Convert a foreign key column of data from a GrowApp table, and convert its values
    to the corresponding foreign key ids in the given Crop db table.

    Foreign key relations from GrowApp tables refer to the IDs in other GrowApp tables.
    This function takes dataframe with such a column, and converts it's values to the
    corresponding IDs in a Crop db table. The pairing is done by looking at the table
    CropDbClass, and matching its `id` column with its `growapp_id` column.

    Parameters
    ==========
    growapp_df: Dataframe of data from a GrowApp table, a foreign key column of which
    needs to be converted to Crop IDs
    growapp_column_name: The name of the column that needs converting
    CropDbClass: The Crop db class from which we should get the new values for the
    foreign key.

    Returns
    =======
    A copy of growapp_df, with values in growapp_column_name replaced with values from
    CropDbClass's id column
    """
    crop_session = get_cropapp_db_session()
    query = crop_session.query(CropDbClass.id, CropDbClass.growapp_id)
    crop_id_pairs = crop_session.execute(query).fetchall()
    session_close(crop_session)
    crop_id_pairs = pd.DataFrame(query_result_to_array(crop_id_pairs)).set_index(
        "growapp_id"
    )
    growapp_df = (
        growapp_df.join(crop_id_pairs, on=growapp_column_name)
        .drop(columns=[growapp_column_name])
        .rename(columns={"id": growapp_column_name})
    )
    return growapp_df


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
        GrowAppCropClass.is_pre_harvest,
    )
    # get the results to an array of dicts before putting into
    # pandas dataframe, to avoid
    # https://github.com/pandas-dev/pandas/issues/40682
    results = session.execute(query).fetchall()
    results_array = query_result_to_array(results)
    crop_df = pd.DataFrame(results_array)
    crop_df.rename(columns={"id": "growapp_id"}, inplace=True)
    session_close(session)
    return crop_df


def get_batch_data():
    """
    Read from the 'Batch' table in the GrowApp database, and transform
    into the format expected by the corresponding table in the CROP db.

    Returns
    =======
    batch_df: pandas DataFrame
    """
    grow_session = get_growapp_db_session()
    query = grow_session.query(
        GrowAppBatchClass.id,
        GrowAppBatchClass.tray_size,
        GrowAppBatchClass.number_of_trays,
        GrowAppBatchClass.crop_id,
    )
    results = grow_session.execute(query).fetchall()
    session_close(grow_session)
    results_array = query_result_to_array(results)
    batch_df = pd.DataFrame(results_array)
    batch_df.rename(columns={"id": "growapp_id"}, inplace=True)

    # we need to get the crop_id from our croptype table
    batch_df = convert_growapp_foreign_key(batch_df, "crop_id", CropTypeClass)
    batch_df = batch_df.rename(columns={"crop_id": "crop_type_id"})
    return batch_df


def get_location_id(growapp_batch_id, growapp_batchevent_type):
    """
    Follow the chain of foreign keys in the growapp database, to get
    an aisle/column/shelf, which we can then use to query the Location
    table in our database, and get a location_id.

    Parameters
    ==========
    growapp_batch_id: uuid, foreign key of the Batch in the Growapp DB
    growapp_batchevent_type: int (maybe we don't care?)
    """
    grow_session = get_growapp_db_session()
    batch_query = grow_session.query(
        GrowBatchClass.current_bench_id
    ).filter(
        GrowBatchClass.id == growap_batch_id
    )
    results = grow_session.execute(batch_query).fetchall()
    results_array = query_result_to_array(results)
    if len(results_array) != 1:
        raise RuntimeError("Couldn't find batch_id {}".format(growapp_batch_id))
    growapp_bench_id = results_array[0]["current_bench_id"]
    # now query the Bench table with that ID
    bench_query = grow_session.query(
        GrowBenchClass.location_id
    ).filter(
        GrowBenchClass.id == growapp_bench_id
    )
    results = grow_session.execute(bench_query).fetchall()
    results_array = query_result_to_array(results)
    if len(results_array) != 1:
        raise RuntimeError("Couldn't find location_id {}".format(growapp_location_id))
    growapp_location_id = results_array[0]["location_id"]
    # now query the Location table with that ID
    location_query = grow_session.query(
        GrowLocationClass.zone_id,
        GrowLocationClass.aisle_id,
        GrowLocationClass.stack_id,
        GrowLocationClass.shelf_id
    ).filter(
        GrowLocationClass.id == growapp_location_id
    )
    results = grow_session.execute(location_query).fetchall()
    results_array = query_result_to_array(results)
    if len(results_array) != 1:
        raise RuntimeError("Couldn't find location_id {}".format(growapp_location_id))
    grow_zone_id = results_array[0]["zone_id"]
    grow_aisle_id = results_array[0]["aisle_id"]
    grow_stack_id = results_array[0]["stack_id"]
    grow_shelf_id = results_array[0]["shelf_id"]
    locname_query = grow_session.query(
        GrowZoneClass.name,
        GrowAisleClass.name.
        GrowStackClass.name,
        GrowShelfClass.name
    ).filter(
        and_(
            GrowZoneClass.id == grow_zone_id,
            GrowAisleClass.id == grow_aisle_id,
            GrowStackClass.id == grow_stack_id,
            GrowShelfClass.id == grow_shelf_id
        )
    )
    results = grow_session.execute(locname_query).fetchall()
    results_array = query_result_to_array(results)
    session_close(grow_session)
    # TODO query our Location table, possibly create new location if this one doesn't yet exist
    return results_array


def get_batchevent_data():
    """
    Read from the 'BatchEvent' table in the GrowApp database, and transform
    into the format expected by the corresponding table in the CROP db.

    Returns
    =======
    batchevent_df: pandas DataFrame
    """
    grow_session = get_growapp_db_session()
    query = grow_session.query(
        GrowAppBatchEventClass.id,
        GrowAppBatchEventClass.type_,
        GrowAppBatchEventClass.was_manual,
        GrowAppBatchEventClass.batch_id,
        GrowAppBatchEventClass.event_happened,
        GrowAppBatchEventClass.description,
        GrowAppBatchEventClass.next_action_days,
        GrowAppBatchEventClass.next_action,
    )
    results = grow_session.execute(query).fetchall()
    session_close(grow_session)
    results_array = query_result_to_array(results)
    batchevents_df = pd.DataFrame(results_array)

    # convert some columns to datetime
    batchevents_df["next_action"] = pd.to_datetime(batchevents_df["next_action"], errors="coerce")
    batchevents_df["event_happened"] = pd.to_datetime(batchevents_df["event_happened"], errors="coerce")
    # look up event type in our scheme
    batchevents_df["type_"] = batchevents_df["type_"].apply(lambda x: BATCH_EVENT_TYPE_MAPPING[x])
    batchevents_df.rename(columns={
        "id": "growapp_id",
        "next_action": "next_action_time",
        "event_happened": "event_time",
        "type_": "event_type"
    }, inplace=True)

    # we need to get the batch_id from our batch table
    batchevents_df = convert_growapp_foreign_key(batchevents_df, "batch_id", BatchClass)
    # TODO Continue here: We need to maybe drop some of the columns of batchevents_df or
    # massage some types, and then, the trickiest part: Get the location_id, by doing
    # some non-trivial joins.
    return batchevents_df


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
    query = session.query(DbClass.growapp_id)
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
    try:
        DbClass.__table__.create(bind=engine)
    except ProgrammingError:
        # The table already exists.
        pass

    existing_growids = get_existing_growapp_ids(session, DbClass)
    if len(existing_growids) > 0:
        existing_index = existing_growids.index
        data_df = data_df[~data_df["growapp_id"].isin(existing_index)]

    logging.info(f"==> Will write {len(data_df)} rows to {DbClass.__tablename__}")
    # loop over all rows in the dataframe
    for _, row in data_df.iterrows():
        new_row = DbClass(**(row.to_dict()))
        session.add(new_row)
    logging.info(f"Finished writing to {DbClass.__tablename__}")
    session.commit()
    session_close(session)
