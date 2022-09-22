"""
Test ingress_weather_forecast.py module
"""

from datetime import datetime, timedelta
from core.ingress_weather_forecast import get_openweathermap_data

dt_to = datetime.utcnow() + timedelta(days=1)

success, error, df = get_openweathermap_data(dt_to)
assert success
