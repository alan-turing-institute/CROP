from app.home import blueprint
from flask import render_template, request
from flask_login import login_required
from sqlalchemy import and_

import copy
from datetime import timedelta

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


@blueprint.route("/<template>")
@login_required
def route_template(template):

    if template == "index21":
        return render_template(template + ".html", jim="Hello")

    return render_template(template + ".html", jim="HEllo")
