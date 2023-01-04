from datetime import datetime, timedelta
from sqlalchemy.orm import Query
import pytest

from core.db import (
    session_close,
)
from core.queries import (
    crop_types,
    latest_sensor_locations,
    latest_trh_locations,
    location_distances,
    sensor_distances,
    closest_trh_sensors,
    first_batch_event_time,
    batch_events_by_type,
    trh_with_vpd,
    trh_sensors_by_zone,
    harvest_with_unit_yield,
    latest_batch_events,
    grow_trh,
    grow_trh_aggregate,
    propagate_trh_aggregate,
    batch_list_with_trh,
    batch_list,
)
from core.structure import ReadingsAranetTRHClass
from .conftest import check_for_docker

DOCKER_RUNNING = check_for_docker()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_crop_types_query(session):
    """
    Test retrieval of crop types
    """
    query = crop_types(session)
    assert isinstance(query, Query)
    assert query.count() == 5
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_latest_sensor_locations_query(session):
    """
    Test query of sensor locations.
    """
    query = latest_sensor_locations(session)
    assert isinstance(query, Query)
    assert query.count() > 0
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_latest_trh_locations_query(session):
    """
    Test query of T&RH sensor locations.
    """
    query = latest_trh_locations(session)
    assert isinstance(query, Query)
    assert query.count() == 2
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_location_distances(session):
    """
    Test query of distances between locations
    """
    query = location_distances(session)
    assert isinstance(query, Query)
    # 12 rows in locations.csv - expect 12^2 results
    assert query.count() == 144
    # query should have three columns
    assert len(query.column_descriptions) == 3
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_closest_trh(session):
    """
    Test query that finds closest sensor for each location
    """
    query = closest_trh_sensors(session)
    assert isinstance(query, Query)
    # 5 Farm1 locations in locations.csv
    assert query.count() == 5
    # query should have twp columns
    assert len(query.column_descriptions) == 2
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_first_batch_event_time(session):
    """
    Test query that finds the earliest batch event
    """
    query = first_batch_event_time(session)
    assert isinstance(query, Query)
    assert query.count() == 1
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_batch_events_by_type(session):
    """
    Test the query that selects batch events according to event type
    """
    query = batch_events_by_type(session, "weigh")
    assert isinstance(query, Query)
    assert query.count() == 4
    query = batch_events_by_type(session, "propagate")
    assert isinstance(query, Query)
    assert query.count() == 4
    query = batch_events_by_type(session, "transfer")
    assert isinstance(query, Query)
    assert query.count() == 4
    query = batch_events_by_type(session, "harvest")
    assert isinstance(query, Query)
    assert query.count() == 4
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_trh_with_vpd(session):
    """
    Test the query that calculates VPD from temperature and humidity
    """
    query = trh_with_vpd(session)
    assert isinstance(query, Query)
    assert query.count() == 115248
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_trh_sensors_by_zone(session):
    """
    Test the query that gets sensors by zone name
    """
    loc_query = latest_trh_locations(session)
    # two sensors in Farm1
    query = trh_sensors_by_zone(session, "Farm1", loc_query)
    assert isinstance(query, Query)
    assert query.count() == 2
    # no sensors in Farm2
    query = trh_sensors_by_zone(session, "Farm2", loc_query)
    assert isinstance(query, Query)
    assert query.count() == 0
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_harvest_with_unit_yield(session):
    """
    Test the query that gets Harvest divided by ntrays*tray_size
    """
    query = harvest_with_unit_yield(session)
    assert isinstance(query, Query)
    assert query.count() == 4
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_latest_batch_events(session):
    """
    Test the query that keeps only the latest batch event of each type
    """
    query = latest_batch_events(session)
    assert isinstance(query, Query)
    # four types of event, four batches with events
    assert query.count() == 16
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_grow_trh(session):
    """
    Test the query that gets TRH+VPD data from sensor closest to location
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)

    query = grow_trh(session, 1, start_time, end_time)
    assert isinstance(query, Query)
    # 6 x 24 x 2
    assert query.count() == 144
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_grow_trh_aggregate(session):
    """
    Test the query that gets average conditions near a batch in grow area
    """
    batch_list_sq = batch_list(session).subquery("batch_list")
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
    query = grow_trh_aggregate(session, batch_list_sq, trh_sq, closest_trh_sensors_cte)
    assert isinstance(query, Query)
    assert len(query.column_descriptions) == 13
    assert query.count() == 4
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_propagate_trh_aggregate(session):
    """
    Test the query that gets average conditions near a batch in grow area
    """
    batch_list_sq = batch_list(session).subquery("batch_list")
    first_event_time_sq = first_batch_event_time(session).subquery("first_event_time")
    trh_q = trh_with_vpd(session).filter(
        ReadingsAranetTRHClass.timestamp >= first_event_time_sq.c.min_time
    )

    latest_trh_locations_cte = latest_trh_locations(session).cte(
        name="latest_trh_locations"
    )

    closest_trh_sensors_cte = closest_trh_sensors(
        session, latest_trh_locations_q=latest_trh_locations_cte
    ).cte(name="closest_trh_sensors_grow_trh_agg")
    query = propagate_trh_aggregate(
        session, batch_list_sq, trh_q, closest_trh_sensors_cte
    )
    assert isinstance(query, Query)
    assert len(query.column_descriptions) == 13
    assert query.count() == 4
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_batch_list_with_trh(session):
    """
    Test the query that lists batches along with environmental conditions
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)

    query = batch_list_with_trh(session)
    assert isinstance(query, Query)
    # 4 batches that went through the farm
    assert query.count() == 4
    # 9 columns
    assert len(query.column_descriptions) == 48
    session_close(session)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_batch_list(session):
    """
    Test the query that lists batches along with lots of other data
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)

    query = batch_list(session)
    assert isinstance(query, Query)
    # 4 batches that went through the farm
    assert query.count() == 4
    # 22 columns
    assert len(query.column_descriptions) == 22
    session_close(session)
