"""
Module for sensor data.
"""
import json
import urllib.parse

from flask import render_template, request
from flask_login import login_required
import pandas as pd
from sqlalchemy import and_

from app.crops import blueprint
from cropcore import queries
from cropcore.structure import SQLA as db
from cropcore.utils import (
    download_csv,
    parse_date_range_argument,
)


@blueprint.route("/batch_list", methods=["GET", "POST"])
@login_required
def batch_list():
    """Render the batch_list page.

    A time range can be provided as a query parameter. For a batch to be included in the
    page, its weigh-event must have happened in this range.
    """
    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))
    subquery = queries.batch_list(db.session).subquery()
    query = (
        db.session.query(subquery)
        .filter(and_(subquery.c.weigh_time >= dt_from, subquery.c.weigh_time <= dt_to))
        .order_by(subquery.c.weigh_time.desc())
    )
    df = pd.read_sql(query.statement, query.session.bind)
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


@blueprint.route("/batch_details", methods=["GET", "POST"])
@login_required
def batch_details():
    """Render the details of a batch."""
    template = "batch_details"
    batch_id = request.args.get("query")
    if batch_id is not None:
        batch_id = int(batch_id)

    subquery = queries.batch_list_with_trh(db.session).subquery()
    query = db.session.query(subquery).filter(subquery.c.batch_id == batch_id)
    details = pd.read_sql(query.statement, query.session.bind).iloc[0, :].to_dict()

    # Get the TRH data for the period this batch was in the main growing area.
    grow_query = queries.grow_trh(
        db.session,
        details["location_id"],
        details["transfer_time"],
        details["harvest_time"],
    )
    grow_trh_df = pd.read_sql(grow_query.statement, grow_query.session.bind)

    if request.method == "POST":
        return download_csv(grow_trh_df, template)
    grow_trh_json = grow_trh_df.to_json(orient="records")
    # TODO Implement comparing some of the data in `details` to averages for the same
    # crop type. See https://github.com/alan-turing-institute/CROP/issues/284
    return render_template(f"{template}.html", details=details, trh_json=grow_trh_json)


@blueprint.route("/harvest_list", methods=["GET", "POST"])
@login_required
def harvest_list():
    """Render the harvest_list page.

    A time range can be provided as a query parameter. For a batch to be included in the
    page, its harvest-event must have happened in this range.
    """
    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))
    subquery = queries.batch_list_with_trh(db.session).subquery()
    query = (
        db.session.query(subquery)
        .filter(
            and_(subquery.c.harvest_time >= dt_from, subquery.c.harvest_time <= dt_to)
        )
        .order_by(subquery.c.harvest_time.desc())
    )
    df = pd.read_sql(query.statement, query.session.bind)
    if "grow_time" in df and len(df["grow_time"]) > 0:
        df["grow_time"] = df["grow_time"].round("s")
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


# This list of dictionaries defines which columns from the batch_list_with_trh query
# will be used in the parallel axes plot, and what they'll be called in the plot. They
# are grouped into groups of axes related to each other, which will affect how they are
# grouped in the UI.
axis_data = [
    {
        "group_name": None,
        "group_members": {
            "yield_per_sqm": {
                "text": "Unit yield (g/sqm)",
                "on_by_default": True,
                "range": None,
            },
            "crop_yield": {
                "text": "Total yield (g)",
                "on_by_default": False,
                "range": None,
            },
            "waste_disease": {
                "text": "Waste disease (%)",
                "on_by_default": True,
                "range": [0, 100],
            },
            "waste_defect": {
                "text": "Waste defect (%)",
                "on_by_default": True,
                "range": [0, 100],
            },
            "over_production": {
                "text": "Over-production (g)",
                "on_by_default": False,
                "range": None,
            },
        },
    },
    {
        "group_name": "Propagation temperature (°C)",
        "group_members": {
            "avg_propagate_temperature": {
                "text": "mean",
                "on_by_default": True,
                "range": None,
            },
            "max_propagate_temperature": {
                "text": "max",
                "on_by_default": False,
                "range": None,
            },
            "min_propagate_temperature": {
                "text": "min",
                "on_by_default": False,
                "range": None,
            },
            "sigma_propagate_temperature": {
                "text": "standard deviation",
                "on_by_default": False,
                "range": None,
            },
        },
    },
    {
        "group_name": "Propagation humidity (%)",
        "group_members": {
            "avg_propagate_humidity": {
                "text": "mean",
                "on_by_default": False,
                "range": None,
            },
            "max_propagate_humidity": {
                "text": "max",
                "on_by_default": False,
                "range": None,
            },
            "min_propagate_humidity": {
                "text": "min",
                "on_by_default": False,
                "range": None,
            },
            "sigma_propagate_humidity": {
                "text": "standard deviation",
                "on_by_default": False,
                "range": None,
            },
        },
    },
    {
        "group_name": "Propagation VPD (Pa)",
        "group_members": {
            "avg_propagate_vpd": {
                "text": "mean",
                "on_by_default": False,
                "range": None,
            },
            "max_propagate_vpd": {
                "text": "max",
                "on_by_default": False,
                "range": None,
            },
            "min_propagate_vpd": {
                "text": "min",
                "on_by_default": False,
                "range": None,
            },
            "sigma_propagate_vpd": {
                "text": "standard deviation",
                "on_by_default": False,
                "range": None,
            },
        },
    },
    {
        "group_name": "Grow temperature (°C)",
        "group_members": {
            "avg_grow_temperature": {
                "text": "mean",
                "on_by_default": True,
                "range": None,
            },
            "max_grow_temperature": {
                "text": "max",
                "on_by_default": False,
                "range": None,
            },
            "min_grow_temperature": {
                "text": "min",
                "on_by_default": False,
                "range": None,
            },
            "sigma_grow_temperature": {
                "text": "standard deviation",
                "on_by_default": False,
                "range": None,
            },
        },
    },
    {
        "group_name": "Grow humidity (%)",
        "group_members": {
            "avg_grow_humidity": {
                "text": "mean",
                "on_by_default": False,
                "range": None,
            },
            "max_grow_humidity": {
                "text": "max",
                "on_by_default": False,
                "range": None,
            },
            "min_grow_humidity": {
                "text": "min",
                "on_by_default": False,
                "range": None,
            },
            "sigma_grow_humidity": {
                "text": "standard deviation",
                "on_by_default": False,
                "range": None,
            },
        },
    },
    {
        "group_name": "Grow VPD (Pa)",
        "group_members": {
            "avg_grow_vpd": {
                "text": "mean",
                "on_by_default": False,
                "range": None,
            },
            "max_grow_vpd": {
                "text": "max",
                "on_by_default": False,
                "range": None,
            },
            "min_grow_vpd": {
                "text": "min",
                "on_by_default": False,
                "range": None,
            },
            "sigma_grow_vpd": {
                "text": "standard deviation",
                "on_by_default": False,
                "range": None,
            },
        },
    },
    {
        "group_name": None,
        "group_members": {
            "grow_time": {
                "text": "Grow time (days)",
                "on_by_default": True,
                "range": None,
            },
            "column": {
                "text": "Column",
                "on_by_default": False,
                "range": None,
            },
            "shelf": {
                "text": "Shelf",
                "on_by_default": True,
                "range": [1, 4],
            },
        },
    },
]


@blueprint.route("/parallel_axes", methods=["GET"])
@login_required
def parallel_axes():
    """Render the parallel axes crop visualisation."""
    dt_from, dt_to = parse_date_range_argument(request.args.get("range"))
    crop_type = request.args.get("crop_type")
    if crop_type is None:
        crop_type = "all"
    else:
        crop_type = urllib.parse.unquote(crop_type)

    squery = queries.batch_list_with_trh(db.session).subquery()
    query = db.session.query(squery).filter(
        and_(
            squery.c.crop_type_name == crop_type if crop_type != "all" else True,
            squery.c.crop_yield.is_not(None),
            squery.c.harvest_time >= dt_from,
            squery.c.harvest_time <= dt_to,
        )
    )
    df = pd.read_sql(query.statement, query.session.bind)
    # Convert some of the timedelta columns to a float of number of days.
    for column_name in ["grow_time"]:
        if len(df[column_name]) > 0:
            df[column_name] = df[column_name].dt.total_seconds() / 3600 / 24

    ct_query = queries.crop_types(db.session)
    crop_types = pd.read_sql(ct_query.statement, ct_query.session.bind).to_dict(
        orient="records"
    )
    crop_types = [{"name": "all"}] + crop_types

    for axis_group in axis_data:
        for axis in axis_group["group_members"].keys():
            assert axis in df.columns

    data_json = df.to_json(orient="columns")
    return render_template(
        "parallel_axes.html",
        data_json=data_json,
        crop_type=crop_type,
        crop_types=crop_types,
        axes=axis_data,
        axes_json=json.dumps(axis_data),
        dt_from=dt_from,
        dt_to=dt_to,
    )
