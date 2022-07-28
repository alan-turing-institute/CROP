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
from urllib import parse

import pandas as pd
from sqlalchemy import and_
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.dialects.postgresql import insert

from __app__.crop.db import connect_db, session_open, session_close
from __app__.crop.structure import (
    LocationClass,
    CropTypeClass,
    BatchClass,
    BatchEventClass,
    HarvestClass,
    EventType,
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
    0: EventType.none,
    10: EventType.weigh,
    20: EventType.propagate,
    30: EventType.transfer,
    40: EventType.harvest,
    99: EventType.edit,
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


def add_new_location(zone, aisle, stack, shelf):
    """
    Add a new location to the CROP database, and return its primary key.

    Parameters
    ==========
    zone: str
    aisle: str
    stack: int (aka column)
    shelf: int

    Returns
    =======
    location_id: int, PK of the newly created location in the CROP DB.
    """
    session = get_cropapp_db_session()
    location = LocationClass(zone=zone, aisle=aisle, column=stack, shelf=shelf)
    session.add(location)
    session.commit()
    id = location.id
    session_close(session)
    print("Returning new location with id {}".format(id))
    return id


def get_location_id(growapp_batch_id):
    """
    Follow the chain of foreign keys in the growapp database, to get an
    aisle/column/shelf, which we can then use to query the Location table in our
    database, and get a location_id.

    Parameters
    ==========
    growapp_batch_id: uuid, foreign key corresponding to the Batch in the Growapp DB

    Raises
    ======
    RuntimeError: If the chain of location information is not found in the GrowApp DB.
    ValueError: If the location is not found in the CROP DB.

    Returns
    =======
    A location ID, i.e. a primary key for the CROP location table.
    """
    print("looking for a location for growapp batch_id {}".format(growapp_batch_id))
    grow_session = get_growapp_db_session()
    batch_query = grow_session.query(GrowAppBatchClass.current_bench_id).filter(
        GrowAppBatchClass.id == growapp_batch_id
    )
    results = grow_session.execute(batch_query).fetchall()
    results_array = query_result_to_array(results)
    if len(results_array) != 1:
        raise RuntimeError("Couldn't find batch_id {}".format(growapp_batch_id))
    growapp_bench_id = results_array[0]["current_bench_id"]
    # now query the Bench table with that ID
    bench_query = grow_session.query(GrowAppBenchClass.location_id).filter(
        GrowAppBenchClass.id == growapp_bench_id
    )
    results = grow_session.execute(bench_query).fetchall()
    results_array = query_result_to_array(results)
    if len(results_array) != 1:
        raise RuntimeError("Couldn't find bench_id {}".format(growapp_bench_id))
    growapp_location_id = results_array[0]["location_id"]
    # now query the Location table with that ID
    location_query = grow_session.query(
        GrowAppLocationClass.zone_id,
        GrowAppLocationClass.aisle_id,
        GrowAppLocationClass.stack_id,
        GrowAppLocationClass.shelf_id,
    ).filter(GrowAppLocationClass.id == growapp_location_id)
    results = grow_session.execute(location_query).fetchall()
    results_array = query_result_to_array(results)
    if len(results_array) != 1:
        raise RuntimeError("Couldn't find location_id {}".format(growapp_location_id))
    grow_zone_id = results_array[0]["zone_id"]
    grow_aisle_id = results_array[0]["aisle_id"]
    grow_stack_id = results_array[0]["stack_id"]
    grow_shelf_id = results_array[0]["shelf_id"]
    locname_query = grow_session.query(
        GrowAppZoneClass.name.label("zone"),
        GrowAppAisleClass.name.label("aisle"),
        GrowAppStackClass.name.label("stack"),
        GrowAppShelfClass.name.label("shelf"),
    ).filter(
        and_(
            GrowAppZoneClass.id == grow_zone_id,
            GrowAppAisleClass.id == grow_aisle_id,
            GrowAppStackClass.id == grow_stack_id,
            GrowAppShelfClass.id == grow_shelf_id,
        )
    )
    results = grow_session.execute(locname_query).fetchall()
    results_array = query_result_to_array(results)
    if len(results_array) > 1:
        raise ValueError("Got multiple locations")
    elif len(results_array) < 1:
        raise ValueError(
            "Couldn't find the GrowApp location "
            f"{grow_zone_id}, {grow_aisle_id}, {grow_stack_id}, {grow_shelf_id}."
        )
    growapp_location = results_array[0]
    session_close(grow_session)
    print(f"Found location {growapp_location}.")
    # fill in missing "zone" by hand
    if not growapp_location["zone"]:
        growapp_location["zone"] = "Farm"
    # Query the Crop Location table to find the corresponding location ID.
    crop_session = get_cropapp_db_session()
    query = crop_session.query(LocationClass.id).filter(
        and_(
            LocationClass.zone == growapp_location["zone"],
            LocationClass.aisle == growapp_location["aisle"],
            LocationClass.column == int(growapp_location["stack"]),
            LocationClass.shelf == int(growapp_location["shelf"]),
        )
    )
    results = crop_session.execute(query).fetchall()
    session_close(crop_session)
    results_array = query_result_to_array(results)
    if len(results_array) == 0:
        print(f"Location {growapp_location} not found in the CROP DB.  Will create it")
        return add_new_location(
            growapp_location["zone"],
            growapp_location["aisle"],
            int(growapp_location["stack"]),
            int(growapp_location["shelf"])
        )
    else:
        return results_array[0]["id"]


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


def get_batch_data(dt_from=None, dt_to=None):
    """
    Read from the 'Batch' table in the GrowApp database, and transform
    into the format expected by the corresponding table in the CROP db.

    Parameters
    ==========
    dt_from, dt_to: datetime, time bounds for the query

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
    if dt_from:
        query = query.filter(
            GrowAppBatchClass.status_date > dt_from
        )
    if dt_to:
        query = query.filter(
            GrowAppBatchClass.status_date < dt_to
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


def get_batchevent_data(dt_from=None, dt_to=None):
    """
    Read from the 'BatchEvent' table in the GrowApp database, and transform
    into the format expected by the corresponding table in the CROP db.

    Parameters
    ==========
    dt_from, dt_to: datetime, time bounds for the query

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
    if dt_from:
        query = query.filter(
            GrowAppBatchEventClass.event_happened > dt_from
        )
    if dt_to:
        query = query.filter(
            GrowAppBatchEventClass.event_happened < dt_to
        )
    results = grow_session.execute(query).fetchall()
    session_close(grow_session)
    results_array = query_result_to_array(results)
    batchevents_df = pd.DataFrame(results_array)

    # convert some columns to datetime
    batchevents_df["next_action"] = pd.to_datetime(
        batchevents_df["next_action"], errors="coerce"
    )
    # convert NaT to None
    batchevents_df["next_action"] = batchevents_df["next_action"].astype(object).where(
        batchevents_df.next_action.notnull(), None
    )
    batchevents_df["event_happened"] = pd.to_datetime(
        batchevents_df["event_happened"], errors="coerce"
    )
    # look up event type in our scheme
    batchevents_df["type_"] = batchevents_df["type_"].apply(
        lambda x: BATCH_EVENT_TYPE_MAPPING[x]
    )
    batchevents_df.rename(
        columns={
            "id": "growapp_id",
            "next_action": "next_action_time",
            "event_happened": "event_time",
            "type_": "event_type",
        },
        inplace=True,
    )
    batchevents_df.loc[:, "location_id"] = None
    transfer_events = batchevents_df.loc[:, "event_type"] == EventType.transfer
    batchevents_df.loc[transfer_events, "location_id"] = batchevents_df.loc[
        transfer_events, "batch_id"
    ].apply(get_location_id)

    # we need to get the batch_id from our batch table
    batchevents_df = convert_growapp_foreign_key(batchevents_df, "batch_id", BatchClass)
    # drop some unused columns
    batchevents_df.drop(columns=["next_action_days", "was_manual", "description"], inplace=True)
    return batchevents_df


def get_harvest_data(dt_from=None, dt_to=None):
    """
    Combine info from the growapp Batch and BatchEvent tables to
    fill a dataframe ready to go into the Harvest table in the CROP db.

    Parameters
    ==========
    dt_from, dt_to: datetime, time bounds for the query

    Returns
    =======
    harvest_df: pandas DataFrame containing all columns needed for the Harvest table.
    """
    grow_session = get_growapp_db_session()
    grow_query = grow_session.query(
        GrowAppBatchClass.id,
        GrowAppBatchClass.harvested_event_id,
        GrowAppBatchClass.yield_,
        GrowAppBatchClass.waste_disease,
        GrowAppBatchClass.waste_defect,
        GrowAppBatchClass.overproduction,
    )
    if dt_from:
        grow_query = grow_query.filter(
            GrowAppBatchClass.status_date > dt_from
        )
    if dt_to:
        grow_query = grow_query.filter(
            GrowAppBatchClass.status_date < dt_to
        )
    results = grow_session.execute(grow_query).fetchall()
    results_array = query_result_to_array(results)
    session_close(grow_session)
    df = pd.DataFrame(results_array)
    df = df[df.harvested_event_id.notnull()]
    df.rename(columns={
        "id": "growapp_id",
        "harvested_event_id": "batch_event_id",
        "yield_": "crop_yield",
        "overproduction": "over_production"
    },inplace=True)
    # get the batchevent_id from our batchevent table
    df = convert_growapp_foreign_key(df, "batch_event_id", BatchEventClass)
    df.loc[:,"location_id"] = df.loc[:,"growapp_id"].apply(get_location_id)
    return df


def get_existing_growapp_ids(session, DbClass):
    """
    Read from the table in the CROP database to get list
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
    Write rows from the input dataframe to the DbClass table in the CROP database.
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

#    existing_growids = get_existing_growapp_ids(session, DbClass)
#    if len(existing_growids) > 0:
#        existing_index = existing_growids.index
#        data_df = data_df[~data_df["growapp_id"].isin(existing_index)]

    logging.info(f"==> Will write {len(data_df)} rows to {DbClass.__tablename__}")
    # loop over all rows in the dataframe
    for _, row in data_df.iterrows():
        insert_stmt = insert(DbClass).values(**(row.to_dict()))
        do_nothing_stmt = insert_stmt.on_conflict_do_nothing( index_elements=['growapp_id'])
        session.execute(do_nothing_stmt)
    logging.info(f"Finished writing to {DbClass.__tablename__}")
    session.commit()
    session_close(session)
    return True



def import_growapp_data(dt_from=None, dt_to=None):
    """
    For initial creation and filling of the CROP database tables, we need to query
    everything in the GrowApp DB.  After that, can use timestamp ranges to filter
    the batch and batchevent queries

    Parameters
    ==========
    dt_from: datetime, starting period for Batch and BatchEvent queries
    dt_to: datetime, ending period for Batch and BatchEvent queries

    Returns
    =======
    success: bool
    """
    success = True
    # always query the whole crop type table - it will be small
    croptype_df = get_croptype_data()
    success &= write_new_data(croptype_df, CropTypeClass)
    batch_df = get_batch_data(dt_from, dt_to)
    success &= write_new_data(batch_df, BatchClass)
    batchevent_df = get_batchevent_data(dt_from, dt_to)
    success &= write_new_data(batchevent_df, BatchEventClass)
    harvest_df = get_harvest_data(dt_from, dt_to)
    success &= write_new_data(harvest_df, HarvestClass)
    return success
