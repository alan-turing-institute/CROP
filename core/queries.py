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


def latest_trh_locations_query(session):
    subquery = session.query(
        SensorLocationClass.sensor_id,
        SensorLocationClass.location_id,
        SensorLocationClass.installation_date,
        func.max(SensorLocationClass.installation_date)
        .over(partition_by=SensorLocationClass.sensor_id)
        .label("max_date"),
    ).subquery()
    latest_trh_locations = (
        session.query(
            subquery.c.sensor_id,
            subquery.c.location_id,
            subquery.c.installation_date,
        )
        .join(SensorClass, SensorClass.id == subquery.c.sensor_id)
        .join(TypeClass, TypeClass.id == SensorClass.type_id)
        .where(
            and_(
                subquery.c.installation_date == subquery.c.max_date,
                TypeClass.sensor_type == "Aranet T&RH",
            )
        )
    )
    return latest_trh_locations


def location_distances_query(session):
    l1 = aliased(LocationClass)
    l2 = aliased(LocationClass)
    location_distances = session.query(
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
    return location_distances


def sensor_distances_query(session, latest_trh_locations=None):
    if latest_trh_locations is None:
        latest_trh_locations = latest_trh_locations_query(session)
    location_distances = location_distances_query(session).cte(
        name="location_distances"
    )
    sensor_distances = session.query(
        location_distances.c.id1.label("location_id"),
        latest_trh_locations.c.sensor_id,
        location_distances.c.distance,
    ).join(
        latest_trh_locations,
        latest_trh_locations.c.location_id == location_distances.c.id2,
    )
    return sensor_distances


def closest_trh_sensors_query(session, latest_trh_locations=None):
    sensor_distances = sensor_distances_query(
        session, latest_trh_locations=latest_trh_locations
    ).cte(name="sensor_distances")
    subquery = (
        session.query(
            sensor_distances.c.location_id,
            sensor_distances.c.sensor_id,
            sensor_distances.c.distance,
            func.min(sensor_distances.c.distance)
            .over(partition_by=sensor_distances.c.location_id)
            .label("min_distance"),
        )
        .filter(sensor_distances.c.sensor_id.is_not(None))
        .subquery()
    )
    closest_trh_sensors = session.query(
        subquery.c.location_id, subquery.c.sensor_id
    ).filter(subquery.c.distance == subquery.c.min_distance)
    return closest_trh_sensors


def first_batch_event_time_query(session):
    first_event_time = session.query(
        func.min(BatchEventClass.event_time).label("min_time")
    )
    return first_event_time


def batch_events_by_type_query(session, type_name):
    events = session.query(
        BatchEventClass.id,
        BatchEventClass.batch_id,
        BatchEventClass.location_id,
        BatchEventClass.event_time,
    ).filter(BatchEventClass.event_type == type_name)
    return events


def trh_data_with_vpd_query(session):
    trh = session.query(
        ReadingsAranetTRHClass.sensor_id,
        ReadingsAranetTRHClass.temperature,
        ReadingsAranetTRHClass.humidity,
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
    )
    return trh


def trh_sensors_by_zone_query(session, zone_name, latest_trh_locations=None):
    if latest_trh_locations is None:
        latest_trh_locations = latest_trh_locations_query(session)
    propagation_trh_sensors = (
        session.query(SensorClass.id)
        .join(latest_trh_locations, latest_trh_locations.c.sensor_id == SensorClass.id)
        .join(LocationClass, LocationClass.id == latest_trh_locations.c.location_id)
        .filter(LocationClass.zone == zone_name)
    )
    return propagation_trh_sensors


def harvest_table_query(session):
    latest_trh_locations = latest_trh_locations_query(session).cte(
        name="latest_trh_locations"
    )
    trh = trh_data_with_vpd_query(session)
    trh_sub = trh.subquery("trh")
    weigh_events = batch_events_by_type_query(session, "weigh").subquery("weigh_events")
    propagate_events = batch_events_by_type_query(session, "propagate").subquery(
        "propagate_events"
    )
    transfer_events = batch_events_by_type_query(session, "transfer").subquery(
        "transfer_events"
    )
    harvest_events = batch_events_by_type_query(session, "harvest").subquery(
        "harvest_events"
    )
    closest_trh_sensors = closest_trh_sensors_query(
        session, latest_trh_locations=latest_trh_locations
    ).cte(name="closest_trh_sensors")
    propagation_trh_sensors = trh_sensors_by_zone_query(
        session, "Propagation", latest_trh_locations=latest_trh_locations
    ).cte("propagation_trh_sensors")

    # Drop all the TRH data from before the first batch event, to make the following
    # queries faster.
    first_event_time = first_batch_event_time_query(session).subquery(
        "first_event_time"
    )
    trh = trh.filter(ReadingsAranetTRHClass.timestamp >= first_event_time.c.min_time)
    trh_sub = trh.subquery("trh")

    grow_trh = (
        session.query(
            BatchClass.id.label("batch_id"),
            func.avg(trh_sub.c.temperature).label("avg_temp"),
            func.avg(trh_sub.c.humidity).label("avg_rh"),
            func.avg(trh_sub.c.vpd).label("avg_vpd"),
        )
        .outerjoin(transfer_events, transfer_events.c.batch_id == BatchClass.id)
        .outerjoin(harvest_events, harvest_events.c.batch_id == BatchClass.id)
        .outerjoin(
            closest_trh_sensors,
            closest_trh_sensors.c.location_id == transfer_events.c.location_id,
        )
        .outerjoin(
            trh_sub,
            and_(
                transfer_events.c.event_time < trh_sub.c.timestamp,
                trh_sub.c.timestamp < harvest_events.c.event_time,
                closest_trh_sensors.c.sensor_id == trh_sub.c.sensor_id,
            ),
        )
        .group_by(BatchClass.id)
    ).subquery("grow_trh")

    trh_prop_sub = trh.filter(
        ReadingsAranetTRHClass.sensor_id.in_(propagation_trh_sensors)
    ).subquery("trh_prop_sub")
    propagate_trh = (
        session.query(
            BatchClass.id.label("batch_id"),
            func.avg(trh_prop_sub.c.temperature).label("avg_temp"),
            func.avg(trh_prop_sub.c.humidity).label("avg_rh"),
            func.avg(trh_prop_sub.c.vpd).label("avg_vpd"),
        )
        .outerjoin(propagate_events, propagate_events.c.batch_id == BatchClass.id)
        .outerjoin(transfer_events, transfer_events.c.batch_id == BatchClass.id)
        .outerjoin(
            trh_prop_sub,
            and_(
                propagate_events.c.event_time < trh_prop_sub.c.timestamp,
                trh_prop_sub.c.timestamp < transfer_events.c.event_time,
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
            weigh_events.c.event_time.label("weigh_time"),
            propagate_events.c.event_time.label("propagate_time"),
            transfer_events.c.event_time.label("transfer_time"),
            harvest_events.c.event_time.label("harvest_time"),
            LocationClass.zone,
            LocationClass.aisle,
            LocationClass.column,
            LocationClass.shelf,
            HarvestClass.crop_yield,
            HarvestClass.waste_disease,
            HarvestClass.waste_defect,
            HarvestClass.over_production,
            (harvest_events.c.event_time - transfer_events.c.event_time).label(
                "grow_time"
            ),
            grow_trh.c.avg_temp.label("avg_grow_temperature"),
            grow_trh.c.avg_rh.label("avg_grow_humidity"),
            grow_trh.c.avg_vpd.label("avg_grow_vpd"),
            propagate_trh.c.avg_temp.label("avg_propagate_temperature"),
            propagate_trh.c.avg_rh.label("avg_propagate_humidity"),
            propagate_trh.c.avg_vpd.label("avg_propagate_vpd"),
        )
        .join(CropTypeClass, CropTypeClass.id == BatchClass.crop_type_id)
        # We inner join on weigh_events, because if the batch doesn't have a weigh event
        # it doesn't really exist, but outer join on the others since they are optional.
        .join(weigh_events, weigh_events.c.batch_id == BatchClass.id)
        .outerjoin(propagate_events, propagate_events.c.batch_id == BatchClass.id)
        .outerjoin(transfer_events, transfer_events.c.batch_id == BatchClass.id)
        .outerjoin(harvest_events, harvest_events.c.batch_id == BatchClass.id)
        .outerjoin(LocationClass, LocationClass.id == transfer_events.c.location_id)
        .outerjoin(HarvestClass, HarvestClass.batch_event_id == harvest_events.c.id)
        .outerjoin(grow_trh, grow_trh.c.batch_id == BatchClass.id)
        .outerjoin(propagate_trh, propagate_trh.c.batch_id == BatchClass.id)
    )
    return query
