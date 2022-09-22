"""
Test ingress_weather.py module
"""

from datetime import datetime, timedelta
from core.ingress_weather import get_openweathermap_data

dt_from = datetime.utcnow() + timedelta(days=-1)
dt_to = datetime.utcnow()

success, error, df = get_openweathermap_data(dt_from, dt_to)
assert success
