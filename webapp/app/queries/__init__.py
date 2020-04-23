from flask import Blueprint

blueprint = Blueprint(
    'queries_blueprint',
    __name__,
    url_prefix='/queries'
)
