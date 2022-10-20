"""
Module for sensor data.
"""
from datetime import datetime
from flask import render_template, request
from flask_login import login_required
import numpy as np
import pandas as pd
from sqlalchemy import and_

from app.crops import blueprint
from core.structure import SQLA as db
from core.structure import (
    BatchClass,
    BatchEventClass,
    CropTypeClass,
    EventType,
    LocationClass,
    HarvestClass,
    ReadingsAranetTRHClass,
    SensorClass,
    SensorLocationClass,
    TypeClass,
)
from core.utils import (
    download_csv,
    filter_latest_sensor_location,
    parse_date_range_argument,
    vapour_pressure_deficit,
)


def collect_batch_details(df_batch):
    """Given a DataFrame that has rows for a given batch only, one per event, construct
    a dictionary of the attributes we care about, discarding others.
    """
    details = {}
    row_weigh = df_batch[df_batch["event_type"] == EventType.weigh]
    row_propagate = df_batch[df_batch["event_type"] == EventType.propagate]
    row_transfer = df_batch[df_batch["event_type"] == EventType.transfer]
    row_harvest = df_batch[df_batch["event_type"] == EventType.harvest]

    if len(row_weigh) > 0:
        # Usually there should only be one event of each type per batch, so just
        # pick the first one.
        row_weigh = row_weigh.iloc[0]
        details["tray_size"] = row_weigh["tray_size"]
        details["number_of_trays"] = row_weigh["number_of_trays"]
        details["crop_type_id"] = row_weigh["crop_type_id"]
        details["crop_type_name"] = row_weigh["crop_type_name"]
        details["weigh_time"] = row_weigh["event_time"]
        details["last_event"] = "weigh"
    else:
        # If there's no weighing event, we don't want to process this batch at all,
        # since we clearly lack meaningful data for it.
        return details

    if len(row_propagate) > 0:
        row_propagate = row_propagate.iloc[0]
        details["propagate_time"] = row_propagate["event_time"]
        details["last_event"] = "propagate"
    else:
        details["propagate_time"] = None

    if len(row_transfer) > 0:
        row_transfer = row_transfer.iloc[0]
        details["location_id"] = row_transfer["location_id"]
        details["zone"] = row_transfer["zone"]
        details["aisle"] = row_transfer["aisle"]
        details["column"] = int(row_transfer["column"])
        details["shelf"] = int(row_transfer["shelf"])
        details["transfer_time"] = row_transfer["event_time"]
        details[
            "location"
        ] = f"{details['zone']} {details['column']}{details['aisle']}{details['shelf']}"
        details["last_event"] = "transfer"
    else:
        details["location_id"] = None
        details["zone"] = None
        details["aisle"] = None
        details["column"] = None
        details["shelf"] = None
        details["location"] = None
        details["transfer_time"] = None

    if len(row_harvest) > 0:
        row_harvest = row_harvest.iloc[0]
        details["crop_yield"] = row_harvest["crop_yield"]
        details["waste_disease"] = row_harvest["waste_disease"]
        details["waste_defect"] = row_harvest["waste_defect"]
        details["over_production"] = row_harvest["over_production"]
        details["harvest_time"] = row_harvest["event_time"]
        details["last_event"] = "harvest"
    else:
        details["crop_yield"] = None
        details["waste_disease"] = None
        details["waste_defect"] = None
        details["over_production"] = None
        details["harvest_time"] = None
    return details


@blueprint.route("/batch_list", methods=["GET", "POST"])
@login_required
def batch_list():
    """Render the batch_list page.

    A time range can be provided as a query parameter. For a batch to be included in the
    page, its weigh-event must have happened in this range. In addition, if other
    events, like harvesting, aren't in the time range, then data from those events is
    left out.
    """
    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    query = (
        db.session.query(
            BatchClass.id.label("batch_id"),
            BatchClass.tray_size,
            BatchClass.number_of_trays,
            BatchClass.crop_type_id.label("batch_crop_type_id"),
            CropTypeClass.id.label("crop_type_id"),
            CropTypeClass.name.label("crop_type_name"),
            BatchEventClass.id.label("batch_event_id"),
            BatchEventClass.batch_id.label("event_batch_id"),
            BatchEventClass.location_id.label("event_location_id"),
            BatchEventClass.event_type,
            BatchEventClass.event_time,
            BatchEventClass.next_action_time,
            HarvestClass.batch_event_id.label("harvest_batch_event_id"),
            HarvestClass.crop_yield,
            HarvestClass.waste_disease,
            HarvestClass.waste_defect,
            HarvestClass.over_production,
            LocationClass.id.label("location_id"),
            LocationClass.zone,
            LocationClass.aisle,
            LocationClass.column,
            LocationClass.shelf,
        )
        .join(CropTypeClass, CropTypeClass.id == BatchClass.crop_type_id)
        .outerjoin(BatchEventClass, BatchEventClass.batch_id == BatchClass.id)
        .outerjoin(HarvestClass, HarvestClass.batch_event_id == BatchEventClass.id)
        .outerjoin(LocationClass, LocationClass.id == BatchEventClass.location_id)
        .filter(
            and_(
                BatchEventClass.event_time >= dt_from,
                BatchEventClass.event_time <= dt_to,
            )
        )
    )
    df_raw = pd.read_sql(query.statement, query.session.bind)

    # Group events by batch, and manually collect the relevant information from each
    # event type, if available. Build a new dataframe with only the information we want,
    # constructing each row as a dictionary first. TODO Might there be a way to lift
    # some of this work over to the Postgres server? Could be faster.
    grouped = df_raw.groupby("batch_id")
    rows = []
    for batch_id, group in grouped:
        details = collect_batch_details(group)
        if details is not None:
            details["batch_id"] = batch_id
            rows.append(details)

    df = pd.DataFrame(
        rows,
        columns=[
            "batch_id",
            "last_event",
            "crop_type_id",
            "crop_type_name",
            "tray_size",
            "number_of_trays",
            "weigh_time",
            "propagate_time",
            "transfer_time",
            "harvest_time",
            "location_id",
            "zone",
            "aisle",
            "column",
            "shelf",
            "location",
            "crop_yield",
            "waste_disease",
            "waste_defect",
            "over_production",
        ],
    )
    # Format the time strings. Easier to do here than in the Jinja template.
    for column in ["weigh_time", "propagate_time", "transfer_time", "harvest_time"]:
        df[column] = pd.to_datetime(df[column]).dt.strftime("%Y-%m-%d %H:%M")
    results_arr = df.to_dict("records")

    if request.method == "POST":
        return download_csv(results_arr, "batch_list")
    else:
        return render_template(
            "batch_list.html",
            batches=results_arr,
            dt_from=dt_from.strftime("%B %d, %Y"),
            dt_to=dt_to.strftime("%B %d, %Y"),
        )


def distance_metric(location1, location2):
    """Compute a custom notion distance between two locations.

    The two locations should be tuples of (zone, aisle, column, shelf).

    The return value is a float.
    """
    zone1, aisle1, column1, shelf1 = location1
    zone2, aisle2, column2, shelf2 = location2
    distance = 0.0
    # TODO Improve this metric.
    if zone1 != zone2:
        distance += 1000.0
    if aisle1 != aisle2:
        distance += 1
    distance += abs(column1 - column2)
    distance += abs(shelf1 - shelf2)
    return distance


def find_closest_trh_sensor(zone, aisle, column, shelf):
    """Return the Aranet TRH sensor ID of the sensor closest to this location."""
    # TODO Move this to utils?
    query = (
        db.session.query(
            SensorClass.id,
            SensorClass.name,
            TypeClass.sensor_type,
            SensorLocationClass.sensor_id,
            SensorLocationClass.location_id,
            SensorLocationClass.installation_date,
            LocationClass.id.label("location_id"),
            LocationClass.zone,
            LocationClass.aisle,
            LocationClass.column,
            LocationClass.shelf,
        )
        .filter(SensorClass.type_id == TypeClass.id)
        .filter(TypeClass.sensor_type == "Aranet T&RH")
        .join(
            SensorLocationClass,
            SensorClass.id == SensorLocationClass.sensor_id,
            isouter=True,
        )
        .join(
            LocationClass,
            LocationClass.id == SensorLocationClass.location_id,
            isouter=True,
        )
        .filter(filter_latest_sensor_location(db))
    )
    df_sensors = pd.read_sql(query.statement, query.session.bind)
    df_sensors["distance"] = df_sensors.apply(
        lambda row: distance_metric(
            (zone, aisle, column, shelf),
            (row["zone"], row["aisle"], row["column"], row["shelf"]),
        ),
        axis=1,
    )
    min_idx = np.argmin(df_sensors["distance"])
    closest_row = df_sensors.loc[min_idx, :]
    return (
        int(closest_row["id"]),
        closest_row["name"],
        closest_row["zone"],
        closest_row["aisle"],
        int(closest_row["column"]),
        int(closest_row["shelf"]),
    )


def query_trh_data(sensor_id, dt_from, dt_to):
    query = db.session.query(
        ReadingsAranetTRHClass.timestamp,
        ReadingsAranetTRHClass.sensor_id,
        ReadingsAranetTRHClass.temperature,
        ReadingsAranetTRHClass.humidity,
    ).filter(
        and_(
            ReadingsAranetTRHClass.sensor_id == sensor_id,
            ReadingsAranetTRHClass.timestamp >= dt_from,
            ReadingsAranetTRHClass.timestamp <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)
    df.loc[:, "vpd"] = vapour_pressure_deficit(
        df.loc[:, "temperature"], df.loc[:, "humidity"]
    )
    return df


def query_propagation_trh_data(dt_from, dt_to):
    query = (
        db.session.query(
            ReadingsAranetTRHClass.timestamp,
            ReadingsAranetTRHClass.sensor_id,
            ReadingsAranetTRHClass.temperature,
            ReadingsAranetTRHClass.humidity,
            SensorClass.id,
            SensorLocationClass.sensor_id,
            SensorLocationClass.location_id,
            SensorLocationClass.installation_date,
            LocationClass.zone,
        )
        .filter(
            and_(
                ReadingsAranetTRHClass.sensor_id == SensorClass.id,
                ReadingsAranetTRHClass.timestamp >= dt_from,
                ReadingsAranetTRHClass.timestamp <= dt_to,
            )
        )
        .join(
            SensorLocationClass,
            SensorClass.id == SensorLocationClass.sensor_id,
            isouter=True,
        )
        .join(
            LocationClass,
            LocationClass.id == SensorLocationClass.location_id,
            isouter=True,
        )
        .filter(filter_latest_sensor_location(db))
        .filter(LocationClass.zone == "Propagation")
    )

    df = pd.read_sql(query.statement, query.session.bind)
    df.loc[:, "vpd"] = vapour_pressure_deficit(
        df.loc[:, "temperature"], df.loc[:, "humidity"]
    )
    return df


def batch_details_trh(details):
    """Get data from the nearest T&RH sensor, for the relevant time period."""
    dt_from = details["transfer_time"]
    dt_to = (
        details["harvest_time"]
        if details["last_event"] == "harvest"
        else datetime.utcnow()
        if details["last_event"] == "transfer"
        else None
    )
    if dt_from and dt_to:
        (
            sensor_id,
            sensor_name,
            sensor_zone,
            sensor_aisle,
            sensor_column,
            sensor_shelf,
        ) = find_closest_trh_sensor(
            details["zone"], details["aisle"], details["column"], details["shelf"]
        )
        trh_df = query_trh_data(sensor_id, dt_from, dt_to)
        trh_summary = {
            "sensor_id": sensor_id,
            "sensor_name": sensor_name,
            "sensor_zone": sensor_zone,
            "sensor_aisle": sensor_aisle,
            "sensor_column": sensor_column,
            "sensor_shelf": sensor_shelf,
            "sensor_location": f"{sensor_zone} {sensor_column}{sensor_aisle}{sensor_shelf}",
            "mean_temperature": np.mean(trh_df.loc[:, "temperature"]),
            "mean_humidity": np.mean(trh_df.loc[:, "humidity"]),
            "mean_vpd": np.mean(trh_df.loc[:, "vpd"]),
        }
    else:
        trh_df = pd.DataFrame()
        trh_summary = {}
    return trh_df, trh_summary


def batch_details_prop_trh(details):
    """Get data from the propagation T&RH sensors for the propagation time period."""
    prop_dt_from = details["propagate_time"]
    prop_dt_to = (
        details["transfer_time"]
        if details["last_event"] in ("transfer", "harvest")
        else datetime.utcnow()
        if details["last_event"] == "propagate"
        else None
    )
    if prop_dt_from and prop_dt_to:
        prop_trh_df = query_propagation_trh_data(prop_dt_from, prop_dt_to)
        prop_trh_summary = {
            "mean_temperature": np.mean(prop_trh_df.loc[:, "temperature"]),
            "mean_humidity": np.mean(prop_trh_df.loc[:, "humidity"]),
            "mean_vpd": np.mean(prop_trh_df.loc[:, "vpd"]),
        }
    else:
        prop_trh_summary = {}
    return prop_trh_summary


@blueprint.route("/batch_details", methods=["GET", "POST"])
@login_required
def batch_details():
    """Render the details of a batch."""
    template = "batch_details"
    batch_id = request.args.get("query")
    if batch_id is not None:
        batch_id = int(batch_id)
    query = (
        db.session.query(
            BatchClass.id.label("batch_id"),
            BatchClass.tray_size,
            BatchClass.number_of_trays,
            BatchClass.crop_type_id.label("batch_crop_type_id"),
            CropTypeClass.id.label("crop_type_id"),
            CropTypeClass.name.label("crop_type_name"),
            BatchEventClass.id.label("batch_event_id"),
            BatchEventClass.batch_id.label("event_batch_id"),
            BatchEventClass.location_id.label("event_location_id"),
            BatchEventClass.event_type,
            BatchEventClass.event_time,
            BatchEventClass.next_action_time,
            HarvestClass.batch_event_id.label("harvest_batch_event_id"),
            HarvestClass.crop_yield,
            HarvestClass.waste_disease,
            HarvestClass.waste_defect,
            HarvestClass.over_production,
            LocationClass.id.label("location_id"),
            LocationClass.zone,
            LocationClass.aisle,
            LocationClass.column,
            LocationClass.shelf,
        )
        .join(CropTypeClass, CropTypeClass.id == BatchClass.crop_type_id)
        .outerjoin(BatchEventClass, BatchEventClass.batch_id == BatchClass.id)
        .outerjoin(HarvestClass, HarvestClass.batch_event_id == BatchEventClass.id)
        .outerjoin(LocationClass, LocationClass.id == BatchEventClass.location_id)
        .filter(BatchClass.id == batch_id)
    )
    df_raw = pd.read_sql(query.statement, query.session.bind)
    details = collect_batch_details(df_raw)
    details["batch_id"] = batch_id
    if len(details) < 2:
        # We know nothing but the batch_id, so render a mostly empty page.
        return render_template(
            f"{template}.html",
            details=details,
            trh_json={},
            trh_summary={},
            prop_trh_summary={},
        )

    if details["harvest_time"] is not None and details["transfer_time"] is not None:
        details["grow_time"] = details["harvest_time"] - details["transfer_time"]
    else:
        details["grow_time"] = None
    if details["crop_yield"] is not None and details["number_of_trays"] is not None:
        # I don't understand meaning of the GrowApp field called tray_size, but it
        # identifies the two different types of trays, and we know from Jakob how many
        # square metres each one is.
        tray_size = details["tray_size"]
        tray_sqm = 0.25 if tray_size == 7.0 else 0.24 if tray_size == 3.0 else np.nan
        details["yield_per_sqm"] = details["crop_yield"] / (
            details["number_of_trays"] * tray_sqm
        )
    else:
        details["yield_per_sqm"] = None

    # Get T&RH sensor data relevant for this batch.
    trh_df, trh_summary = batch_details_trh(details)
    prop_trh_summary = batch_details_prop_trh(details)

    # Format some of the fields to be strings. Easier to do here than in the Jinja
    # template.
    for column in ["weigh_time", "propagate_time", "transfer_time", "harvest_time"]:
        if details[column] is not None:
            details[column] = pd.to_datetime(details[column]).strftime("%Y-%m-%d %H:%M")
    if details["yield_per_sqm"] is not None:
        details["yield_per_sqm"] = f"{details['yield_per_sqm']:.1f}"

    if request.method == "POST":
        return download_csv(trh_df, template)
    trh_json = trh_df.to_json(orient="records")
    # TODO Implement comparing some of the data in `details` to averages for the same
    # crop type. See https://github.com/alan-turing-institute/CROP/issues/284
    return render_template(
        f"{template}.html",
        details=details,
        trh_json=trh_json,
        trh_summary=trh_summary,
        prop_trh_summary=prop_trh_summary,
    )


@blueprint.route("/harvest_list", methods=["GET", "POST"])
@login_required
def harvest_list():
    """Render the harvest_list page.

    A time range can be provided as a query parameter. For a batch to be included in the
    page, its harvest-event must have happened in this range.
    """
    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

    # TODO Convert all this into SQLAlchemy calls. Reuse those calls in batch_list and
    # batch_details. Then tune performance.
    sql_query_string = """
        WITH latest_trh_locations AS (
            SELECT ss.sensor_id, ss.location_id, ss.installation_date
            FROM (
                SELECT
                    sensor_id,
                    location_id,
                    installation_date,
                    max(installation_date) OVER (PARTITION BY sensor_id) AS max_date
                FROM sensor_location
            ) AS ss
            JOIN sensors
            ON (sensors.id = ss.sensor_id)
            JOIN sensor_types
            ON (sensors.type_id = sensor_types.id)
            WHERE ss.installation_date = ss.max_date
            AND sensor_types.sensor_type = 'Aranet T&RH'
        ),

        location_distances AS (
            SELECT
            l1.id AS id1,
            l2.id AS id2,
            (
                (CASE WHEN l1.zone = l2.zone THEN 0 ELSE NULL END)
                + (CASE WHEN l1.aisle = l2.aisle THEN 0 ELSE 1 END)
                + abs(l1.column - l2.column)
                + abs(l1.shelf - l2.shelf)
            ) AS distance
            FROM locations l1, locations l2
        ),

        sensor_distances AS (
            SELECT
                location_distances.id1 AS location_id,
                latest_trh_locations.sensor_id,
                location_distances.distance
            FROM location_distances
            JOIN latest_trh_locations
            ON latest_trh_locations.location_id = location_distances.id2
        ),

        closests_trh_sensors AS (
            SELECT ss.location_id, ss.sensor_id
            FROM (
                SELECT
                    location_id,
                    sensor_id,
                    distance,
                    min(distance) OVER (PARTITION BY location_id) AS min_distance
                FROM sensor_distances
                WHERE sensor_id IS NOT NULL
            ) AS ss
            WHERE ss.distance = ss.min_distance
        ),

        first_event_time AS (
            SELECT min(event_time) as min_time
            FROM batch_events
        )

        SELECT
            batches.id AS batch_id,
            crop_types.name AS crop_type_name,
            batches.tray_size,
            batches.number_of_trays,
            weigh_events.event_time AS weigh_time,
            propagate_events.event_time AS propagate_time,
            transfer_events.event_time AS transfer_time,
            locations.zone,
            locations.aisle,
            locations.column,
            locations.shelf,
            harvest_events.event_time AS harvest_time,
            harvests.crop_yield,
            harvests.waste_disease,
            harvests.waste_defect,
            harvests.over_production,
            harvest_events.event_time - transfer_events.event_time AS grow_time,
            grow_trh.avg_temp AS avg_grow_temperature,
            grow_trh.avg_rh AS avg_grow_humidity,
            grow_trh.avg_vpd AS avg_grow_vpd,
            propagate_trh.avg_temp AS avg_propagation_temperature,
            propagate_trh.avg_rh AS avg_propagation_humidity,
            propagate_trh.avg_vpd AS avg_propagation_vpd
        FROM batches

        INNER JOIN
        crop_types
        ON (batches.crop_type_id = crop_types.id)

        INNER JOIN (
            SELECT batch_id, event_time
            FROM batch_events
            WHERE batch_events.event_type = 'weigh'
        )
        AS weigh_events
        ON (batches.id = weigh_events.batch_id)

        LEFT OUTER JOIN (
            SELECT batch_id, event_time
            FROM batch_events
            WHERE batch_events.event_type = 'propagate'
        )
        AS propagate_events
        ON (batches.id = propagate_events.batch_id)

        LEFT OUTER JOIN (
            SELECT batch_id, event_time, location_id
            FROM batch_events
            WHERE batch_events.event_type = 'transfer'
        )
        AS transfer_events
        ON (batches.id = transfer_events.batch_id)

        LEFT OUTER JOIN (
            SELECT id, batch_id, event_time
            FROM batch_events
            WHERE batch_events.event_type = 'harvest'
        )
        AS harvest_events
        ON (batches.id = harvest_events.batch_id)

        LEFT OUTER JOIN
        locations ON (locations.id = transfer_events.location_id)

        LEFT OUTER JOIN
        harvests ON (harvests.batch_event_id = harvest_events.id)

        LEFT OUTER JOIN (
            SELECT
                batches.id AS batch_id,
                avg(trh.temperature) AS avg_temp,
                avg(trh.humidity) AS avg_rh,
                avg(trh.vpd) AS avg_vpd
            FROM batches
            LEFT OUTER JOIN (
                SELECT batch_id, event_time, location_id
                FROM batch_events
                WHERE batch_events.event_type = 'transfer'
            )
            AS transfer_events
            ON (batches.id = transfer_events.batch_id)
            LEFT OUTER JOIN (
                SELECT id, batch_id, event_time
                FROM batch_events
                WHERE batch_events.event_type = 'harvest'
            )
            AS harvest_events
            ON (batches.id = harvest_events.batch_id)
            LEFT OUTER JOIN
            closests_trh_sensors
            ON transfer_events.location_id = closests_trh_sensors.location_id
            LEFT OUTER JOIN (
                SELECT
                    sensor_id,
                    temperature,
                    humidity,
                    (
                        610.78
                        * exp(17.2694 * temperature / (temperature + 237.3))
                        * (1.0 - humidity / 100.0)
                    ) AS vpd,
                    timestamp
                FROM aranet_trh_data
            )
            AS trh
            ON (
                trh.timestamp BETWEEN transfer_events.event_time
                AND harvest_events.event_time
                AND closests_trh_sensors.sensor_id = trh.sensor_id
            )
            GROUP BY batches.id
        ) AS grow_trh
        ON (grow_trh.batch_id = batches.id)

        LEFT OUTER JOIN (
            WITH propagation_trh_sensors AS (
                SELECT sensors.id
                FROM sensors
                JOIN latest_trh_locations
                ON latest_trh_locations.sensor_id = sensors.id
                JOIN locations
                ON locations.id = latest_trh_locations.location_id
                WHERE (locations.zone = 'Propagation')
            )
            SELECT
                batches.id AS batch_id,
                avg(trh.temperature) AS avg_temp,
                avg(trh.humidity) AS avg_rh,
                avg(trh.vpd) AS avg_vpd
            FROM batches
            LEFT OUTER JOIN (
                SELECT batch_id, event_time
                FROM batch_events
                WHERE batch_events.event_type = 'propagate'
            ) AS propagate_events
            ON (batches.id = propagate_events.batch_id)
            LEFT OUTER JOIN (
                SELECT id, batch_id, event_time
                FROM batch_events
                WHERE batch_events.event_type = 'transfer'
            ) AS transfer_events
            ON (batches.id = transfer_events.batch_id)
            LEFT OUTER JOIN (
                SELECT
                    sensor_id,
                    temperature,
                    humidity,
                    (
                        610.78
                        * exp(17.2694 * temperature / (temperature + 237.3))
                        * (1.0 - humidity / 100.0)
                    ) AS vpd,
                    timestamp
                FROM aranet_trh_data
                WHERE (sensor_id IN (SELECT id FROM propagation_trh_sensors))
            ) AS trh
            ON (
                trh.timestamp
                BETWEEN propagate_events.event_time
                AND transfer_events.event_time
            )
            GROUP BY batches.id
        ) AS propagate_trh
        ON (propagate_trh.batch_id = batches.id)
        ;
        """

    query_result = db.session.execute(sql_query_string)
    df = pd.DataFrame(query_result.fetchall(), columns=query_result.keys())

    # Format the time strings and some numerical fields. Easier to do here than in the
    # Jinja template.
    for column in ["harvest_time"]:
        if column in df:
            df[column] = pd.to_datetime(df[column]).dt.strftime("%Y-%m-%d %H:%M")
    if "grow_time" in df:
        df["grow_time"] = df["grow_time"].round("s")
    for column in [
        "avg_propagation_temperature",
        "avg_propagation_humidity",
        "avg_propagation_vpd",
        "avg_grow_temperature",
        "avg_grow_humidity",
        "avg_grow_vpd",
    ]:
        if column in df:
            df[column] = df[column].apply(lambda x: f"{x:.2f}")
    results_arr = df.to_dict("records")

    if request.method == "POST":
        return download_csv(results_arr, "harvest_list")
    else:
        return render_template(
            "harvest_list.html",
            batches=results_arr,
            dt_from=dt_from.strftime("%B %d, %Y"),
            dt_to=dt_to.strftime("%B %d, %Y"),
        )
