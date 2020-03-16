from flask import Blueprint

blueprint = Blueprint(
    'locations_blueprint',
    __name__,
    url_prefix='/locations',
    template_folder='templates',
    static_folder='static'
)
