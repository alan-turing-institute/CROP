from flask import Blueprint

blueprint = Blueprint(
    "readings_blueprint",
    __name__,
    url_prefix="/readings",
    template_folder="templates",
    static_folder="static",
)
