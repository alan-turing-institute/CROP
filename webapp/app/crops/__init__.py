from flask import Blueprint

blueprint = Blueprint(
    "crops_blueprint",
    __name__,
    url_prefix="/crops",
    template_folder="templates",
    static_folder="static",
)
