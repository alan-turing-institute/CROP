from flask import Flask, url_for
from flask_login import LoginManager, login_required
from flask_cors import CORS

from importlib import import_module
from logging import basicConfig, DEBUG, getLogger, StreamHandler
from os import path

from cropcore.constants import (
    DEFAULT_USER_USERNAME,
    DEFAULT_USER_EMAIL,
    DEFAULT_USER_PASS,
)
from cropcore.structure import SQLA as db
from cropcore.structure import UserClass
from cropcore.utils import change_user_password, create_user, delete_user


login_manager = LoginManager()


@login_manager.user_loader
def user_loader(id):
    return UserClass.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get("username")
    user = UserClass.query.filter_by(username=username).first()
    return user if user else None


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)


def register_blueprints(app):
    module_list = (
        "base",
        "crops",
        "dashboards",
        "home",
        "locations",
        "logs",
        "predictions",
        "queries",
        "readings",
        "sensors",
        "types",
        "users",
    )

    for module_name in module_list:
        module = import_module("app.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)


def register_template_filters(app):
    @app.template_filter()
    def format_datetime(value):
        try:
            return value.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            return value


def configure_database(app):
    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def configure_logs(app):
    basicConfig(filename="error.log", level=DEBUG)
    logger = getLogger()
    logger.addHandler(StreamHandler())


def apply_themes(app):
    """
    Add support for themes.

    If DEFAULT_THEME is set then all calls to
      url_for('static', filename='')
      will modfify the url to include the theme name

    The theme parameter can be set directly in url_for as well:
      ex. url_for('static', filename='', theme='')

    If the file cannot be found in the /static/<theme>/ lcation then
      the url will not be modified and the file is expected to be
      in the default /static/ location
    """

    @app.context_processor
    def override_url_for():
        return dict(url_for=_generate_url_for_theme)

    def _generate_url_for_theme(endpoint, **values):
        if endpoint.endswith("static"):
            themename = values.get("theme", None) or app.config.get(
                "DEFAULT_THEME", None
            )
            if themename:
                theme_file = "{}/{}".format(themename, values.get("filename", ""))
                if path.isfile(path.join(app.static_folder, theme_file)):
                    values["filename"] = theme_file
        return url_for(endpoint, **values)


def add_default_user(app):
    """Ensure that there's a default user from CROP, with the right credentials."""
    with app.app_context():
        if DEFAULT_USER_PASS is None:
            delete_user(username=DEFAULT_USER_USERNAME, email=DEFAULT_USER_EMAIL)
        else:
            user_info = {
                "username": DEFAULT_USER_USERNAME,
                "email": DEFAULT_USER_EMAIL,
                "password": DEFAULT_USER_PASS,
            }
            success, _ = create_user(**user_info)
            if not success:
                # Presumably the user exists already, so change their password.
                change_user_password(**user_info)


def create_app(config, selenium=False):
    app = Flask(__name__, static_folder="base/static")
    app.config.from_object(config)

    if selenium:
        app.config["LOGIN_DISABLED"] = True
    register_extensions(app)
    register_blueprints(app)
    register_template_filters(app)
    configure_database(app)
    configure_logs(app)
    apply_themes(app)
    CORS(app)
    add_default_user(app)
    return app
