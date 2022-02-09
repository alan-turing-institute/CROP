from flask import Blueprint

blueprint = Blueprint(
    "predictions_blueprint",
    __name__,
    url_prefix="/predictions",
    template_folder="templates",
    static_folder="static",
)
