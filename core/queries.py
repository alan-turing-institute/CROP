"""Functions for building various database queries.

Each function return a SQLAlchemy Query object. Turning these into subqueries or CTEs is
the responsibility of the caller.
"""
from sqlalchemy import and_, case, func
from sqlalchemy.orm import aliased

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
    subquery = latest_sensor_locations(session).subquery()
    query = (
        session.query(subquery)
        .join(SensorClass, SensorClass.id == subquery.c.sensor_id)
        .join(TypeClass, TypeClass.id == SensorClass.type_id)
        .where(TypeClass.sensor_type == "Aranet T&RH")
    )
    return query


def location_distances(session):
    l1 = aliased(LocationClass)
    l2 = aliased(LocationClass)
    query = session.query(
        l1.id.label("id1"),
        l2.id.label("id2"),
        (
            case([(l1.zone == l2.zone, 0)], else_=None)
            + case(
                [(l1.aisle == l2.aisle, 0)], else_=1
            )  # TODO Is this line working?  Check the query string.
            + func.abs(l1.column - l2.column)
            + func.abs(l1.shelf - l2.shelf)
        ).label("distance"),
    )
    return query


def sensor_distances(session, latest_trh_locations_q=None):
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
    query = session.query(func.min(BatchEventClass.event_time).label("min_time"))
    return query


def batch_events_by_type(session, type_name):
    subquery = latest_batch_events(session).subquery()
    query = session.query(subquery).filter(subquery.c.event_type == type_name)
    return query


def trh_with_vpd(session):
    """Query that is like the ReadingsAranetTRHClass, except it has the extra column
    "vpd" for vapour pressure deficit.
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
    if latest_trh_locations_q is None:
        latest_trh_locations_q = latest_trh_locations(session)
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
    """A query that's like the harvest table, but with a column yield_per_sqm."""
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
    """A query like the batch events table, but filter to only keep the latest instance
    of each (batch_id, event_type) pair, e.g. if the same batch has multiple "propagate"
    events only keep the last.
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


def grow_trh_aggregate(
    session, trh_sq, transfer_events_sq, harvest_events_sq, closest_trh_sensors_cte
):
    query = (
        session.query(
            BatchClass.id.label("batch_id"),
            func.avg(trh_sq.c.temperature).label("avg_temp"),
            func.avg(trh_sq.c.humidity).label("avg_rh"),
            func.avg(trh_sq.c.vpd).label("avg_vpd"),
        )
        .outerjoin(transfer_events_sq, transfer_events_sq.c.batch_id == BatchClass.id)
        .outerjoin(harvest_events_sq, harvest_events_sq.c.batch_id == BatchClass.id)
        .outerjoin(
            closest_trh_sensors_cte,
            closest_trh_sensors_cte.c.location_id == transfer_events_sq.c.location_id,
        )
        .outerjoin(
            trh_sq,
            and_(
                transfer_events_sq.c.event_time < trh_sq.c.timestamp,
                trh_sq.c.timestamp < harvest_events_sq.c.event_time,
                closest_trh_sensors_cte.c.sensor_id == trh_sq.c.sensor_id,
            ),
        )
        .group_by(BatchClass.id)
    )
    return query


def propagate_trh_aggregate(
    session, trh_q, propagate_events_sq, transfer_events_sq, latest_trh_locations_q
):
    propagation_trh_sensors_cte = trh_sensors_by_zone(
        session, "Propagation", latest_trh_locations_q=latest_trh_locations_q
    ).cte("propagation_trh_sensors")
    trh_prop_sq = trh_q.filter(
        ReadingsAranetTRHClass.sensor_id.in_(propagation_trh_sensors_cte)
    ).subquery("trh_prop_sq")
    query = (
        session.query(
            BatchClass.id.label("batch_id"),
            func.avg(trh_prop_sq.c.temperature).label("avg_temp"),
            func.avg(trh_prop_sq.c.humidity).label("avg_rh"),
            func.avg(trh_prop_sq.c.vpd).label("avg_vpd"),
        )
        .outerjoin(propagate_events_sq, propagate_events_sq.c.batch_id == BatchClass.id)
        .outerjoin(transfer_events_sq, transfer_events_sq.c.batch_id == BatchClass.id)
        .outerjoin(
            trh_prop_sq,
            and_(
                propagate_events_sq.c.event_time < trh_prop_sq.c.timestamp,
                trh_prop_sq.c.timestamp < transfer_events_sq.c.event_time,
            ),
        )
        .group_by(BatchClass.id)
    )
    return query


# TODO harvest_list duplicates a lot of batch_list, they should probably rather use each
# other.
def harvest_table(session):
    latest_trh_locations_cte = latest_trh_locations(session).cte(
        name="latest_trh_locations"
    )
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

    # Drop all the TRH data from before the first batch event, to make the following
    # queries faster.
    first_event_time_sq = first_batch_event_time(session).subquery("first_event_time")
    trh_q = trh_with_vpd(session).filter(
        ReadingsAranetTRHClass.timestamp >= first_event_time_sq.c.min_time
    )
    trh_sq = trh_q.subquery("trh")

    closest_trh_sensors_cte = closest_trh_sensors(
        session, latest_trh_locations_q=latest_trh_locations_cte
    ).cte(name="closest_trh_sensors_grow_trh_agg")
    grow_trh_sq = grow_trh_aggregate(
        session, trh_sq, transfer_events_sq, harvest_events_sq, closest_trh_sensors_cte
    ).subquery("grow_trh")

    propagate_trh_sq = propagate_trh_aggregate(
        session,
        trh_q,
        propagate_events_sq,
        transfer_events_sq,
        latest_trh_locations_cte,
    ).subquery("propagate_trh")

    harvest_sq = harvest_with_unit_yield(session).subquery("harvest_with_unit_yield")

    locations_sq = locations_with_extras(session).subquery("locations")
    locations_sq2 = aliased(locations_sq)

    query = (
        session.query(
            BatchClass.id.label("batch_id"),
            CropTypeClass.name.label("crop_type_name"),
            BatchClass.tray_size,
            BatchClass.number_of_trays,
            weigh_events_sq.c.event_time.label("weigh_time"),
            propagate_events_sq.c.event_time.label("propagate_time"),
            transfer_events_sq.c.event_time.label("transfer_time"),
            harvest_events_sq.c.event_time.label("harvest_time"),
            locations_sq.c.id.label("location_id"),
            locations_sq.c.zone,
            locations_sq.c.aisle,
            locations_sq.c.column,
            locations_sq.c.shelf,
            locations_sq.c.summary.label("location_summary"),
            SensorClass.name.label("closest_sensor_name"),
            locations_sq2.c.summary.label("sensor_location_summary"),
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
            grow_trh_sq.c.avg_temp.label("avg_grow_temperature"),
            grow_trh_sq.c.avg_rh.label("avg_grow_humidity"),
            grow_trh_sq.c.avg_vpd.label("avg_grow_vpd"),
            propagate_trh_sq.c.avg_temp.label("avg_propagate_temperature"),
            propagate_trh_sq.c.avg_rh.label("avg_propagate_humidity"),
            propagate_trh_sq.c.avg_vpd.label("avg_propagate_vpd"),
        )
        .join(CropTypeClass, CropTypeClass.id == BatchClass.crop_type_id)
        # We inner join on weigh_events, because if the batch doesn't have a weigh event
        # it doesn't really exist, but outer join on the others since they are optional.
        .join(weigh_events_sq, weigh_events_sq.c.batch_id == BatchClass.id)
        .outerjoin(propagate_events_sq, propagate_events_sq.c.batch_id == BatchClass.id)
        .outerjoin(transfer_events_sq, transfer_events_sq.c.batch_id == BatchClass.id)
        .outerjoin(harvest_events_sq, harvest_events_sq.c.batch_id == BatchClass.id)
        .outerjoin(locations_sq, locations_sq.c.id == transfer_events_sq.c.location_id)
        .outerjoin(
            closest_trh_sensors_cte,
            closest_trh_sensors_cte.c.location_id == transfer_events_sq.c.location_id,
        )
        .outerjoin(SensorClass, SensorClass.id == closest_trh_sensors_cte.c.sensor_id)
        .outerjoin(
            latest_trh_locations_cte,
            latest_trh_locations_cte.c.sensor_id == SensorClass.id,
        )
        .outerjoin(
            locations_sq2, locations_sq2.c.id == latest_trh_locations_cte.c.location_id
        )
        .outerjoin(harvest_sq, harvest_sq.c.batch_event_id == harvest_events_sq.c.id)
        .outerjoin(grow_trh_sq, grow_trh_sq.c.batch_id == BatchClass.id)
        .outerjoin(propagate_trh_sq, propagate_trh_sq.c.batch_id == BatchClass.id)
    )
    return query


def batch_list(session):
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
    """Return the locations table but with a an extra columns for what we call "region"
    and for summarising the location in a single string.

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
