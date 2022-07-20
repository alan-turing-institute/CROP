"""
Python module to read from the PurpleCrane GrowApp database, and write to CROP database
"""
import logging
import time
from datetime import datetime, timedelta
import requests
import pandas as pd

from sqlalchemy import and_
from sqlalchemy.exc import ProgrammingError

from __app__.crop.db import connect_db, session_open, session_close
from __app__.crop.structure import (
    LocationClass,
    CropTypeClass,
    BatchClass,
    BatchEventClass,
    HarvestClass,
)

from __app__.crop.growapp_structure import (
    LocationClass as GrowAppLocationClass,
    CropClass as GrowAppCropClass,
    BatchClass as GrowAppBatchClass,
    BatchEventClass as GrowAppBatchEventClass,
)

from __app__.crop.utils import query_result_to_array
from __app__.crop.constants import (
    GROWAPP_IP,
    GROWAPP_DB,
    GROWAPP_USER,
    GROWAPP_PASSWORD,
    GROWAPP_SCHEMA,
)

from __app__.crop.ingress import log_upload_event
