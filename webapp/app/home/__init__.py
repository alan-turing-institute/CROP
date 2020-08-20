from flask import Blueprint

blueprint = Blueprint(
    'views_blueprint',
    __name__,
    url_prefix='/home',
    template_folder='templates',
    static_folder='static'
)
