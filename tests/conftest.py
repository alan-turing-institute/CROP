import sys
import pytest

from webapp.app import create_app
from webapp.config import config_dict
from core.constants import SQL_CONNECTION_STRING, SQL_TEST_DBNAME
from core.db import drop_db
from util_scripts import upload_synthetic_data

sys.path.append("webapp")


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """

    print("pytest_configure: start " + SQL_CONNECTION_STRING + " " + SQL_TEST_DBNAME)

    upload_synthetic_data.main(SQL_TEST_DBNAME)

    print("pytest_configure: end")


def pytest_unconfigure(config):
    """
    called before test process is exited.
    """

    print("pytest_unconfigure: start")

    # drops test db
    success, log = drop_db(SQL_CONNECTION_STRING, SQL_TEST_DBNAME)
    assert success, log

    print("pytest_unconfigure: end")


@pytest.fixture()
def app():
    config = config_dict["Production"]
    app = create_app(config)
    app.config.update(
        {
            "TESTING": True,
        }
    )

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
