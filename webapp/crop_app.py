from flask_migrate import Migrate
from os import environ
from sys import exit
import sys

sys.path.append("..")
from werkzeug.middleware.proxy_fix import ProxyFix
from config import config_dict
from app import create_app, db

get_config_mode = environ.get("CROP_CONFIG_MODE", "Production")

try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit("Error: Invalid CROP_CONFIG_MODE environment variable entry.")

app = create_app(config_mode)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

Migrate(app, db)
