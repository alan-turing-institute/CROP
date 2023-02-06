"""Functions for building various database queries.

Each function return a SQLAlchemy Query object. Turning these into subqueries or CTEs is
the responsibility of the caller.
"""
from sqlalchemy import and_, case, func
from sqlalchemy.orm import aliased, Query

from core.structure import (
    BatchClass,
    BatchEventClass,
    CropTypeClass,
    LocationClass,
    HarvestClass,
    ReadingsAranetTRHClass,
    SensorClass,
    SensorLocationClass,
    TypeClass,
)

# The last columns considered to be in FrontFarm and MidFarm, respectively.
REGION_SPLIT_FRONT_MID = 10
REGION_SPLIT_MID_BACK = 23


def crop_types(session):
    query = session.query(CropTypeClass.name)
    return query


def latest_sensor_locations(session):
    """A query like SensorLocationClass, but with only one row per sensor, the one with
    the most recent installation date.
    """
    subquery = session.query(
        SensorLocationClass,
        func.max(SensorLocationClass.installation_date)
        .over(partition_by=SensorLocationClass.sensor_id)
        .label("max_date"),
    ).subquery()
    query = session.query(subquery).where(
        subquery.c.installation_date == subquery.c.max_date
    )
    return query


def latest_trh_locations(session):
    """A query like latest_sensor_locations, but restricted to Aranet T&RH sensors
    only.
    """
    subquery = latest_sensor_locations(session).subquery()
    query = (
        session.query(subquery)
        .join(SensorClass, SensorClass.id == subquery.c.sensor_id)
        .join(TypeClass, TypeClass.id == SensorClass.type_id)
        .where(TypeClass.sensor_type == "Aranet T&RH")
    )
    return query


def location_distances(session):
    """A query with three columns: id1, id2, which are location ids, and distance, which
    is the distance metric value for those two locations.

    We define our distance metric as follows: It's None/null (representing infinity) if
    the locations are in different zones, otherwise it is
    the difference in the column numbers
    + the difference in shelf numbers
    + 1 if the locations are on different aisles.
    """
    l1 = aliased(LocationClass)
    l2 = aliased(LocationClass)
    query = session.query(
        l1.id.label("id1"),
        l2.id.label("id2"),
        (
            case([(l1.zone == l2.zone, 0)], else_=None)
            + case([(l1.aisle == l2.aisle, 0)], else_=1)
            + func.abs(l1.column - l2.column)
            + func.abs(l1.shelf - l2.shelf)
        ).label("distance"),
    )
    return query


def sensor_distances(session, latest_trh_locations_q=None):
    """Query with three columns: location_id, sensor_id, and distance, that measures the
    distance between each sensor and location.

    See location_distances for how the distance metric is defined.
    """
    if latest_trh_locations_q is None:
        latest_trh_locations_q = latest_trh_locations(session).subquery(
            "latest_trh_locations_sensor_distances"
        )
    location_distances_cte = location_distances(session).cte(name="location_distances")
    query = session.query(
        location_distances_cte.c.id1.label("location_id"),
        latest_trh_locations_q.c.sensor_id,
        location_distances_cte.c.distance,
    ).join(
        latest_trh_locations_q,
        latest_trh_locations_q.c.location_id == location_distances_cte.c.id2,
    )
    return query


def closest_trh_sensors(session, latest_trh_locations_q=None):
    """Query with two columns: location_id (for every location there is) and sensor_id
    for the T&RH sensor closest to that location.
    """
    sensor_distances_cte = sensor_distances(
        session, latest_trh_locations_q=latest_trh_locations_q
    ).cte(name="sensor_distances")
    subquery = (
        session.query(
            sensor_distances_cte,
            func.min(sensor_distances_cte.c.distance)
            .over(partition_by=sensor_distances_cte.c.location_id)
            .label("min_distance"),
        )
        .filter(sensor_distances_cte.c.sensor_id.is_not(None))
        .subquery()
    )
    query = session.query(subquery.c.location_id, subquery.c.sensor_id).filter(
        subquery.c.distance == subquery.c.min_distance
    )
    return query


def first_batch_event_time(session):
    """Query for the time of the first event in BatchEventClass."""
    query = session.query(func.min(BatchEventClass.event_time).label("min_time"))
    return query


def batch_events_by_type(session, type_name):
    """Query for all BatchEventClass rows of the type given by type_name."""
    subquery = latest_batch_events(session).subquery()
    query = session.query(subquery).filter(subquery.c.event_type == type_name)
    return query


def trh_with_vpd(session):
    """Query like ReadingsAranetTRHClass, except with the extra column "vpd" for vapour
    pressure deficit.
    """
    query = session.query(
        ReadingsAranetTRHClass,
        # This called the Tetens equations, see
        # https://en.wikipedia.org/wiki/Tetens_equation and
        # https://pulsegrow.com/blogs/learn/vpd.
        # The outcome is the vapour pressure deficit in Pascals.
        (
            610.78
            * func.exp(
                17.2694
                * ReadingsAranetTRHClass.temperature
                / (ReadingsAranetTRHClass.temperature + 237.3)
            )
            * (1.0 - ReadingsAranetTRHClass.humidity / 100.0)
        ).label("vpd"),
    )
    return query


def trh_sensors_by_zone(session, zone_name, latest_trh_locations_q=None):
    """Query with one column, `id`, for the ids of all the sensors in zone zone_name."""
    if latest_trh_locations_q is None:
        latest_trh_locations_q = latest_trh_locations(session).subquery()
    elif isinstance(latest_trh_locations_q, Query):
        latest_trh_locations_q = latest_trh_locations_q.subquery()
    query = (
        session.query(SensorClass.id)
        .join(
            latest_trh_locations_q,
            latest_trh_locations_q.c.sensor_id == SensorClass.id,
        )
        .join(LocationClass, LocationClass.id == latest_trh_locations_q.c.location_id)
        .filter(LocationClass.zone == zone_name)
    )
    return query


def harvest_with_unit_yield(session):
    """Query like HarvestClass but with a column yield_per_sqm."""
    query = (
        session.query(
            HarvestClass,
            # Crop yield divided by number of trays * tray size.
            (
                HarvestClass.crop_yield
                / (
                    BatchClass.number_of_trays
                    * case(
                        [
                            # Tray size in square metres.
                            # TODO This information is very non-obvious, and should
                            # probably be stored somewhere other than hardcoded here.
                            (BatchClass.tray_size == 7.0, 0.25),
                            (BatchClass.tray_size == 3.0, 0.24),
                        ],
                        else_=None,
                    )
                )
            ).label("yield_per_sqm"),
        )
        .join(BatchEventClass, HarvestClass.batch_event_id == BatchEventClass.id)
        .join(BatchClass, BatchEventClass.batch_id == BatchClass.id)
    )
    return query


def latest_batch_events(session):
    """Query like BatchEventClass, but filtered to only keep the latest instance of each
    (batch_id, event_type) pair, e.g. if the same batch has multiple "propagate" events
    only keep the last.
    """
    subquery = session.query(
        BatchEventClass,
        func.max(BatchEventClass.event_time)
        .over(partition_by=(BatchEventClass.batch_id, BatchEventClass.event_type))
        .label("latest_time"),
    ).subquery()
    query = session.query(subquery).where(
        subquery.c.event_time == subquery.c.latest_time
    )
    return query


def grow_trh(session, location_id, start_time, end_time, latest_trh_locations_q=None):
    """Query of T&RH data (with VPD) from the sensor closest to location_id, within the
    time window from start_time to end_time.
    """
    # "infinity" is a special value understood by postgres
    if start_time is None:
        start_time = "infinity"
    if end_time is None:
        end_time = "infinity"
    closest_trh_sensors_cte = closest_trh_sensors(
        session, latest_trh_locations_q=latest_trh_locations_q
    ).subquery(name="closest_trh_sensors")
    trh_sq = trh_with_vpd(session).subquery("trh_with_vpd")
    query = session.query(trh_sq).filter(
        and_(
            start_time < trh_sq.c.timestamp,
            trh_sq.c.timestamp < end_time,
            closest_trh_sensors_cte.c.location_id == location_id,
            closest_trh_sensors_cte.c.sensor_id == trh_sq.c.sensor_id,
        ),
    )
    return query


def grow_trh_aggregate(session, batches_sq, trh_sq, closest_trh_sensors_cte):
    """Query with four columns: batch_id, avg_temp, avg_rh, and avg_vpd, where the last
    three are means of T&RH values over the period from transfer time to harvest time
    from the closest sensor for each batch.

    trh_sq is the T&RH subquery to use for getting the T&RH data, batches_sq is a query
    (probably the output of batch_list) with columns for batch_id, location_id,
    transfer_time, and harvest_time.
    """
    query = (
        session.query(
            batches_sq.c.batch_id,
            func.avg(trh_sq.c.temperature).label("avg_temp"),
            func.avg(trh_sq.c.humidity).label("avg_rh"),
            func.avg(trh_sq.c.vpd).label("avg_vpd"),
            func.min(trh_sq.c.temperature).label("min_temp"),
            func.min(trh_sq.c.humidity).label("min_rh"),
            func.min(trh_sq.c.vpd).label("min_vpd"),
            func.max(trh_sq.c.temperature).label("max_temp"),
            func.max(trh_sq.c.humidity).label("max_rh"),
            func.max(trh_sq.c.vpd).label("max_vpd"),
            func.stddev_samp(trh_sq.c.temperature).label("sigma_temp"),
            func.stddev_samp(trh_sq.c.humidity).label("sigma_rh"),
            func.stddev_samp(trh_sq.c.vpd).label("sigma_vpd"),
        )
        .outerjoin(
            closest_trh_sensors_cte,
            closest_trh_sensors_cte.c.location_id == batches_sq.c.location_id,
        )
        .outerjoin(
            trh_sq,
            and_(
                batches_sq.c.transfer_time < trh_sq.c.timestamp,
                trh_sq.c.timestamp < batches_sq.c.harvest_time,
                closest_trh_sensors_cte.c.sensor_id == trh_sq.c.sensor_id,
            ),
        )
        .group_by(batches_sq.c.batch_id)
    )
    return query


def propagate_trh_aggregate(session, batches_sq, trh_q, latest_trh_locations_q):
    """Query with four columns: batch_id, avg_temp, avg_rh, and avg_vpd, where the last
    three are means of T&RH values over the period from propagation time to transfer
    time for each batch from the propagation sensors.

    trh_sq is the T&RH subquery to use for getting the T&RH data, batches_sq is a query
    (probably the output of batch_list) with columns for batch_id, propagate_time, and
    transfer_time.
    """
    propagation_trh_sensors_cte = trh_sensors_by_zone(
        session, "Propagation", latest_trh_locations_q=latest_trh_locations_q
    ).cte("propagation_trh_sensors")
    trh_prop_sq = trh_q.filter(
        ReadingsAranetTRHClass.sensor_id.in_(propagation_trh_sensors_cte)
    ).subquery("trh_prop_sq")
    query = (
        session.query(
            batches_sq.c.batch_id,
            func.avg(trh_prop_sq.c.temperature).label("avg_temp"),
            func.avg(trh_prop_sq.c.humidity).label("avg_rh"),
            func.avg(trh_prop_sq.c.vpd).label("avg_vpd"),
            func.min(trh_prop_sq.c.temperature).label("min_temp"),
            func.min(trh_prop_sq.c.humidity).label("min_rh"),
            func.min(trh_prop_sq.c.vpd).label("min_vpd"),
            func.max(trh_prop_sq.c.temperature).label("max_temp"),
            func.max(trh_prop_sq.c.humidity).label("max_rh"),
            func.max(trh_prop_sq.c.vpd).label("max_vpd"),
            func.stddev_samp(trh_prop_sq.c.temperature).label("sigma_temp"),
            func.stddev_samp(trh_prop_sq.c.humidity).label("sigma_rh"),
            func.stddev_samp(trh_prop_sq.c.vpd).label("sigma_vpd"),
        )
        .outerjoin(
            trh_prop_sq,
            and_(
                batches_sq.c.propagate_time < trh_prop_sq.c.timestamp,
                trh_prop_sq.c.timestamp < batches_sq.c.transfer_time,
            ),
        )
        .group_by(batches_sq.c.batch_id)
    )
    return query


def batch_list_with_trh(session):
    """Query like batch_list, but with columns for information about the nearest sensor,
    and T&RH growing and propagation conditions.

    The added columns are called closest_sensor_name, sensor_location_summary,
    avg_grow_temperature, avg_grow_humidity, avg_grow_vpd, avg_propagate_temperature,
    avg_propagate_humidity, and avg_propagate_vpd.
    """
    batch_list_sq = batch_list(session).subquery("batch_list")

    # Drop all the TRH data from before the first batch event, to make the following
    # queries faster.
    first_event_time_sq = first_batch_event_time(session).subquery("first_event_time")
    trh_q = trh_with_vpd(session).filter(
        ReadingsAranetTRHClass.timestamp >= first_event_time_sq.c.min_time
    )
    trh_sq = trh_q.subquery("trh")

    latest_trh_locations_cte = latest_trh_locations(session).cte(
        name="latest_trh_locations"
    )

    closest_trh_sensors_cte = closest_trh_sensors(
        session, latest_trh_locations_q=latest_trh_locations_cte
    ).cte(name="closest_trh_sensors_grow_trh_agg")
    grow_trh_sq = grow_trh_aggregate(
        session, batch_list_sq, trh_sq, closest_trh_sensors_cte
    ).subquery("grow_trh")

    propagate_trh_sq = propagate_trh_aggregate(
        session, batch_list_sq, trh_q, latest_trh_locations_cte
    ).subquery("propagate_trh")

    locations_sq = locations_with_extras(session).subquery("locations2")

    query = (
        session.query(
            batch_list_sq,
            SensorClass.name.label("closest_sensor_name"),
            locations_sq.c.summary.label("sensor_location_summary"),
            grow_trh_sq.c.avg_temp.label("avg_grow_temperature"),
            grow_trh_sq.c.avg_rh.label("avg_grow_humidity"),
            grow_trh_sq.c.avg_vpd.label("avg_grow_vpd"),
            propagate_trh_sq.c.avg_temp.label("avg_propagate_temperature"),
            propagate_trh_sq.c.avg_rh.label("avg_propagate_humidity"),
            propagate_trh_sq.c.avg_vpd.label("avg_propagate_vpd"),
            grow_trh_sq.c.min_temp.label("min_grow_temperature"),
            grow_trh_sq.c.min_rh.label("min_grow_humidity"),
            grow_trh_sq.c.min_vpd.label("min_grow_vpd"),
            propagate_trh_sq.c.min_temp.label("min_propagate_temperature"),
            propagate_trh_sq.c.min_rh.label("min_propagate_humidity"),
            propagate_trh_sq.c.min_vpd.label("min_propagate_vpd"),
            grow_trh_sq.c.max_temp.label("max_grow_temperature"),
            grow_trh_sq.c.max_rh.label("max_grow_humidity"),
            grow_trh_sq.c.max_vpd.label("max_grow_vpd"),
            propagate_trh_sq.c.max_temp.label("max_propagate_temperature"),
            propagate_trh_sq.c.max_rh.label("max_propagate_humidity"),
            propagate_trh_sq.c.max_vpd.label("max_propagate_vpd"),
            grow_trh_sq.c.sigma_temp.label("sigma_grow_temperature"),
            grow_trh_sq.c.sigma_rh.label("sigma_grow_humidity"),
            grow_trh_sq.c.sigma_vpd.label("sigma_grow_vpd"),
            propagate_trh_sq.c.sigma_temp.label("sigma_propagate_temperature"),
            propagate_trh_sq.c.sigma_rh.label("sigma_propagate_humidity"),
            propagate_trh_sq.c.sigma_vpd.label("sigma_propagate_vpd"),
        )
        # We inner join on weigh_events, because if the batch doesn't have a weigh event
        # it doesn't really exist, but outer join on the others since they are optional.
        .outerjoin(
            closest_trh_sensors_cte,
            closest_trh_sensors_cte.c.location_id == batch_list_sq.c.location_id,
        )
        .outerjoin(SensorClass, SensorClass.id == closest_trh_sensors_cte.c.sensor_id)
        .outerjoin(
            latest_trh_locations_cte,
            latest_trh_locations_cte.c.sensor_id == SensorClass.id,
        )
        .outerjoin(
            locations_sq, locations_sq.c.id == latest_trh_locations_cte.c.location_id
        )
        .outerjoin(grow_trh_sq, grow_trh_sq.c.batch_id == batch_list_sq.c.batch_id)
        .outerjoin(
            propagate_trh_sq, propagate_trh_sq.c.batch_id == batch_list_sq.c.batch_id
        )
    )
    return query


def batch_list(session):
    """Query for all sorts of data related to batches, one row per batch.

    Columns included are:
    batch_id,
    tray_size,
    number_of_trays,
    crop_type_id,
    crop_type_name,
    weigh_time,
    propagate_time,
    transfer_time,
    harvest_time,
    location_id,
    zone (zone, aisle, column, and shelf are for the location in the main farm),
    aisle,
    column,
    shelf,
    location_summary,
    yield_per_sqm,
    crop_yield,
    waste_disease,
    waste_defect,
    over_production,
    grow_time,
    last_event (one of "weigh", "propagate", "transfer", or "harvest").

    Batches that don't have even a weighing event are not included in the query. Batches
    that have multiple cases of the same event (e.g. two propagation events) only have
    the latest of each event type included.
    """
    weigh_events_sq = batch_events_by_type(session, "weigh").subquery("weigh_events")
    propagate_events_sq = batch_events_by_type(session, "propagate").subquery(
        "propagate_events"
    )
    transfer_events_sq = batch_events_by_type(session, "transfer").subquery(
        "transfer_events"
    )
    harvest_events_sq = batch_events_by_type(session, "harvest").subquery(
        "harvest_events"
    )
    harvest_sq = harvest_with_unit_yield(session).subquery("harvest_with_unit_yield")
    locations_sq = locations_with_extras(session).subquery("locations")

    query = (
        session.query(
            BatchClass.id.label("batch_id"),
            BatchClass.tray_size,
            BatchClass.number_of_trays,
            CropTypeClass.id.label("crop_type_id"),
            CropTypeClass.name.label("crop_type_name"),
            weigh_events_sq.c.event_time.label("weigh_time"),
            propagate_events_sq.c.event_time.label("propagate_time"),
            transfer_events_sq.c.event_time.label("transfer_time"),
            harvest_events_sq.c.event_time.label("harvest_time"),
            transfer_events_sq.c.next_action_time.label("expected_harvest_time"),
            locations_sq.c.id.label("location_id"),
            locations_sq.c.zone,
            locations_sq.c.aisle,
            locations_sq.c.column,
            locations_sq.c.shelf,
            locations_sq.c.summary.label("location_summary"),
            harvest_sq.c.yield_per_sqm,
            harvest_sq.c.crop_yield,
            harvest_sq.c.waste_disease,
            harvest_sq.c.waste_defect,
            harvest_sq.c.over_production,
            (harvest_events_sq.c.event_time - transfer_events_sq.c.event_time).label(
                "grow_time"
            ),
            case(
                [
                    (harvest_events_sq.c.event_time != None, "harvest"),
                    (transfer_events_sq.c.event_time != None, "transfer"),
                    (propagate_events_sq.c.event_time != None, "propagate"),
                    (weigh_events_sq.c.event_time != None, "weigh"),
                ],
                else_=None,
            ).label("last_event"),
        )
        .join(CropTypeClass, CropTypeClass.id == BatchClass.crop_type_id)
        # We inner join on weigh_events, because if the batch doesn't have a weigh event
        # it doesn't really exist, but outer join on the others since they are optional.
        .join(weigh_events_sq, weigh_events_sq.c.batch_id == BatchClass.id)
        .outerjoin(propagate_events_sq, propagate_events_sq.c.batch_id == BatchClass.id)
        .outerjoin(transfer_events_sq, transfer_events_sq.c.batch_id == BatchClass.id)
        .outerjoin(harvest_events_sq, harvest_events_sq.c.batch_id == BatchClass.id)
        .outerjoin(locations_sq, locations_sq.c.id == transfer_events_sq.c.location_id)
        .outerjoin(harvest_sq, harvest_sq.c.batch_event_id == harvest_events_sq.c.id)
    )
    return query


def locations_with_extras(session):
    """Query like LocationClass but with extra columns for what we call "region" and for
    summarising the location in a single string, called "summary".

    Region distinguishes between front, back, and mid parts of tunnel 3. Propagation and
    R&D are regions by themselves, other tunnels have region "N/A".
    """
    query = session.query(
        LocationClass,
        case(
            [
                (LocationClass.zone == "R&D", "R&D"),
                (LocationClass.zone == "Propagation", "Propagation"),
                (
                    LocationClass.zone == "Tunnel3",
                    case(
                        [
                            (
                                LocationClass.column <= REGION_SPLIT_FRONT_MID,
                                "FrontFarm",
                            ),
                            (
                                and_(
                                    REGION_SPLIT_FRONT_MID < LocationClass.column,
                                    LocationClass.column <= REGION_SPLIT_MID_BACK,
                                ),
                                "MidFarm",
                            ),
                            (
                                REGION_SPLIT_MID_BACK < LocationClass.column,
                                "BackFarm",
                            ),
                        ]
                    ),
                ),
            ],
            else_="N/A",
        ).label("region"),
        func.concat(
            LocationClass.zone,
            case(
                [
                    (
                        LocationClass.column != None,
                        func.concat(" ", LocationClass.column),
                    )
                ]
            ),
            case([(LocationClass.aisle != None, LocationClass.aisle)]),
            case([(LocationClass.shelf != None, LocationClass.shelf)]),
        ).label("summary"),
    )
    return query
