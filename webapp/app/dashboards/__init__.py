from flask import Blueprint

blueprint = Blueprint(
    'home_blueprint',
    __name__,
    url_prefix='/dashboards',
    template_folder='templates',
    static_folder='static'
)
