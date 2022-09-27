"""
Module for sensor data.
"""

from flask import render_template, request
from flask_login import login_required
from sqlalchemy import and_, desc
import pandas as pd
import io

from app.crops import blueprint
from core.utils import (
    query_result_to_array,
    parse_date_range_argument,
    download_csv,
)

from core.structure import SQLA as db
from core.structure import (
    BatchClass,
    BatchEventClass,
    CropTypeClass,
    EventType,
    LocationClass,
    HarvestClass,
)


@blueprint.route("/batch_list", methods=["GET"])
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
        row = {"batch_id": batch_id}
        row_weigh = group[group["event_type"] == EventType.weigh]
        row_propagate = group[group["event_type"] == EventType.propagate]
        row_transfer = group[group["event_type"] == EventType.transfer]
        row_harvest = group[group["event_type"] == EventType.harvest]

        if len(row_weigh) > 0:
            # Usually there should only be one event of each type per batch, so just
            # pick the first one.
            row_weigh = row_weigh.iloc[0]
            row["tray_size"] = row_weigh["tray_size"]
            row["number_of_trays"] = row_weigh["number_of_trays"]
            row["crop_type_id"] = row_weigh["crop_type_id"]
            row["crop_type_name"] = row_weigh["crop_type_name"]
            row["weigh_time"] = row_weigh["event_time"]
            row["last_event"] = "weigh"
            # At this point we have enough data to at least have some kind of row in the
            # table. The following parts modify `row` in-place.
            rows.append(row)
        else:
            # If we don't have the weighing event for this batch, we don't want to
            # process any of the others either. This is to avoid confusing cases where
            # e.g. the harvest event was in the time range provided but the weighing
            # wasn't and thus there would be a row with data missing.
            continue

        if len(row_propagate) > 0:
            row_propagate = row_propagate.iloc[0]
            row["propagate_time"] = row_propagate["event_time"]
            row["last_event"] = "propagate"

        if len(row_transfer) > 0:
            row_transfer = row_transfer.iloc[0]
            row["location_id"] = row_transfer["location_id"]
            row["zone"] = row_transfer["zone"]
            row["aisle"] = row_transfer["aisle"]
            row["shelf"] = row_transfer["shelf"]
            row["transfer_time"] = row_transfer["event_time"]
            row["last_event"] = "transfer"

        if len(row_harvest) > 0:
            row_harvest = row_harvest.iloc[0]
            row["crop_yield"] = row_harvest["crop_yield"]
            row["waste_disease"] = row_harvest["waste_disease"]
            row["waste_defect"] = row_harvest["waste_defect"]
            row["over_production"] = row_harvest["over_production"]
            row["harvest_time"] = row_harvest["event_time"]
            row["last_event"] = "harvest"

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
            "shelf",
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

    return render_template(
        "batch_list.html",
        batches=results_arr,
        dt_from=dt_from.strftime("%B %d, %Y"),
        dt_to=dt_to.strftime("%B %d, %Y"),
    )
