from sqlalchemy.orm import Query

from core.constants import SQL_CONNECTION_STRING, SQL_TEST_DBNAME
from core.db import (
    connect_db,
    session_open,
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
)


def test_crop_types_query():
    """
    Test retrieval of crop types
    """
    status, log, engine = connect_db(SQL_CONNECTION_STRING, SQL_TEST_DBNAME)
    session = session_open(engine)
    query = crop_types(session)
    assert isinstance(query, Query)
    assert query.count() == 5
    session_close(session)


def test_latest_sensor_locations_query():
    """
    Test query of sensor locations.
    """
