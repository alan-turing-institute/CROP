from app.home import blueprint
from flask import render_template, request
from flask_login import login_required
from sqlalchemy import and_

import copy

# import datetime as dt

import numpy as np
import pandas as pd

import logging


from utilities.utils import parse_date_range_argument

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass,
    LocationClass,
    SensorLocationClass,
    ReadingsZensieTRHClass,
)
from __app__.crop.constants import CONST_MAX_RECORDS, CONST_TIMESTAMP_FORMAT


def zensie_query(dt_from, dt_to, location_zone):
    """
    Performs data analysis for Zensie sensors.

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
    Returns:
        sensor_names: a list of sensor names
        sensor_temp_ranges: json data with temperate ranges
    """

    logging.info(
        "Calling zensie_analysis with parameters %s %s"
        % (
            dt_from.strftime(CONST_TIMESTAMP_FORMAT),
            dt_to.strftime(CONST_TIMESTAMP_FORMAT),
        )
    )

    query = db.session.query(
        ReadingsZensieTRHClass.timestamp,
        ReadingsZensieTRHClass.sensor_id,
        SensorClass.name,
        ReadingsZensieTRHClass.temperature,
        ReadingsZensieTRHClass.humidity,
    ).filter(
        and_(
            LocationClass.zone == location_zone,
            SensorLocationClass.location_id == LocationClass.id,  # propagation location
            # ReadingsZensieTRHClass.sensor_id == SensorClass.id,
            ReadingsZensieTRHClass.sensor_id == SensorLocationClass.sensor_id,
            ReadingsZensieTRHClass.timestamp >= dt_from,
            ReadingsZensieTRHClass.timestamp <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    logging.info("Total number of records found: %d" % (len(df.index)))

    if not df.empty:
        sensor_names = "mods"
        sensor_temp_ranges = "meh"
        # sensor_names, sensor_temp_ranges = temperature_range_analysis(
        #    df, dt_from, dt_to
        # )

    else:
        sensor_names = []
        sensor_temp_ranges = {}

    return sensor_names, sensor_temp_ranges


# zensie_query(dt_from, dt_to, "Propagation")


@blueprint.route("/<template>")
@login_required
def route_template(template):

    # dt_to = dt.datetime.now()
    # dt_from = dt_to - dt.timedelta(days=7)
    # a, b = zensie_query(dt_from, dt_to, "Propagation")
    a = "hello"
    if template == "index21":
        return render_template(template + ".html", jim=a)

    return render_template(template + ".html", jim=a)
