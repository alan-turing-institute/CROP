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
        SensorLocationClass.sensor_id,
        SensorLocationClass.location_id,
        SensorLocationClass.installation_date,
        func.max(SensorLocationClass.installation_date)
        .over(partition_by=SensorLocationClass.sensor_id)
        .label("max_date"),
    ).subquery()
    query = session.query(
        subquery.c.sensor_id,
        subquery.c.location_id,
        subquery.c.installation_date,
    ).where(subquery.c.installation_date == subquery.c.max_date)
    return query


def latest_trh_locations(session):
    subquery = latest_sensor_locations(session).subquery()
    query = (
        session.query(
            subquery.c.sensor_id,
            subquery.c.location_id,
            subquery.c.installation_date,
        )
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
        latest_trh_locations_q = latest_trh_locations(session)
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
            sensor_distances_cte.c.location_id,
            sensor_distances_cte.c.sensor_id,
            sensor_distances_cte.c.distance,
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
    query = session.query(
        BatchEventClass.id,
        BatchEventClass.batch_id,
        BatchEventClass.location_id,
        BatchEventClass.event_time,
    ).filter(BatchEventClass.event_type == type_name)
    return query


def trh_with_vpd(session):
    """Query that is like the ReadingsAranetTRHClass, except it has the extra column
    "vpd" for vapour pressure deficit.
    """
    query = session.query(
        ReadingsAranetTRHClass.sensor_id,
        ReadingsAranetTRHClass.temperature,
        ReadingsAranetTRHClass.humidity,
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
        ReadingsAranetTRHClass.timestamp,
        ReadingsAranetTRHClass.time_created,
        ReadingsAranetTRHClass.time_updated,
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
    closest_trh_sensors_cte = closest_trh_sensors(
        session, latest_trh_locations_q=latest_trh_locations_cte
    ).cte(name="closest_trh_sensors")
    propagation_trh_sensors_cte = trh_sensors_by_zone(
        session, "Propagation", latest_trh_locations_q=latest_trh_locations_cte
    ).cte("propagation_trh_sensors")

    # Drop all the TRH data from before the first batch event, to make the following
    # queries faster.
    first_event_time_sq = first_batch_event_time(session).subquery("first_event_time")
    trh_q = trh_with_vpd(session).filter(
        ReadingsAranetTRHClass.timestamp >= first_event_time_sq.c.min_time
    )
    trh_sq = trh_q.subquery("trh")

    grow_trh_sq = (
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
    ).subquery("grow_trh")

    trh_prop_sq = trh_q.filter(
        ReadingsAranetTRHClass.sensor_id.in_(propagation_trh_sensors_cte)
    ).subquery("trh_prop_sq")
    propagate_trh_sq = (
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
    ).subquery("propagate_trh")

    query = (
        session.query(
            BatchClass.id.label("batch_id"),
            CropTypeClass.name.label("crop_type_name"),
            BatchClass.tray_size,
            BatchClass.number_of_trays,
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
            weigh_events_sq.c.event_time.label("weigh_time"),
            propagate_events_sq.c.event_time.label("propagate_time"),
            transfer_events_sq.c.event_time.label("transfer_time"),
            harvest_events_sq.c.event_time.label("harvest_time"),
            LocationClass.zone,
            LocationClass.aisle,
            LocationClass.column,
            LocationClass.shelf,
            HarvestClass.crop_yield,
            HarvestClass.waste_disease,
            HarvestClass.waste_defect,
            HarvestClass.over_production,
            (harvest_events_sq.c.event_time - transfer_events_sq.c.event_time).label(
                "grow_time"
            ),
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
        .outerjoin(LocationClass, LocationClass.id == transfer_events_sq.c.location_id)
        .outerjoin(HarvestClass, HarvestClass.batch_event_id == harvest_events_sq.c.id)
        .outerjoin(grow_trh_sq, grow_trh_sq.c.batch_id == BatchClass.id)
        .outerjoin(propagate_trh_sq, propagate_trh_sq.c.batch_id == BatchClass.id)
    )
    return query


def locations_with_regions(session):
    """Return the locations table but with a an extra column for what we call "region".

    Region distinguishes between front, back, and mid parts of tunnel 3. Propagation and
    R&D are regions by themselves, other tunnels have region "N/A".
    """
    query = session.query(
        LocationClass.id,
        LocationClass.zone,
        LocationClass.aisle,
        LocationClass.column,
        LocationClass.shelf,
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
    )
    return query
