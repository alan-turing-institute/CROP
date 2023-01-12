"""
Test the routes that show sensor readings
"""

import pytest

from .conftest import check_for_docker

DOCKER_RUNNING = check_for_docker()

# use the testuser fixture to add a user to the database
@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_user(testuser):
    assert True


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_energy_readings(client):
    # login
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "test", "login": "login"},
    )
    # should get a redirect
    assert response.status_code == 302
    response = client.get("/readings/energy")
    assert response.status_code == 200
    html_content = response.data.decode("utf-8")
    # check header for energy data
    assert "<h3>Uploaded Energy Data <small>" in html_content
    # check we have a table
    assert '<table id="datatable-responsive"' in html_content


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_trh_readings(client):
    # login
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "test", "login": "login"},
    )
    # should get a redirect
    assert response.status_code == 302
    response = client.get("/readings/aranet_trh")
    assert response.status_code == 200
    html_content = response.data.decode("utf-8")
    assert (
        "<title>CROP |  Aranet Temperature and Relative Humidity Data </title>"
        in html_content
    )
    assert '<table id="datatable-responsive"' in html_content
    # check we have some rows
    assert html_content.count("<tr>") > 8000  # seems to vary..?


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_co2_readings(client):
    # login
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "test", "login": "login"},
    )
    # should get a redirect
    assert response.status_code == 302
    response = client.get("/readings/aranet_co2")
    assert response.status_code == 200
    html_content = response.data.decode("utf-8")
    assert "<title>CROP |  Aranet CO2 Data </title>" in html_content
    assert '<table id="datatable-responsive"' in html_content
    # check we have some rows
    assert html_content.count("<tr>") > 1000  # seems to vary..?


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_air_velocity_readings(client):
    # login
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "test", "login": "login"},
    )
    # should get a redirect
    assert response.status_code == 302
    response = client.get("/readings/aranet_air_velocity")
    assert response.status_code == 200
    html_content = response.data.decode("utf-8")
    assert "<title>CROP |  Aranet Air Velocity Data </title>" in html_content
    assert '<table id="datatable-responsive"' in html_content
    # check we have some rows
    assert html_content.count("<tr>") > 1000  # seems to vary..?
