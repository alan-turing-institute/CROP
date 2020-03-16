from flask import Blueprint

blueprint = Blueprint(
    'sensors_blueprint',
    __name__,
    url_prefix='/sensors',
    template_folder='templates',
    static_folder='static'
)
