from flask import Blueprint

blueprint = Blueprint(
    'types_blueprint',
    __name__,
    url_prefix='/types',
    template_folder='templates',
    static_folder='static'
)
