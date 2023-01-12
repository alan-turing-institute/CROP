"""
Test the routes defined in webapp/app/sensors/routes.py
"""

import pytest

from .conftest import check_for_docker

DOCKER_RUNNING = check_for_docker()


# use the testuser fixture to add a user to the database
@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_user(testuser):
    assert True


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_sensor_list_not_logged_in(client):
    response = client.get("/sensors/sensor_list")
    assert response.status_code == 401


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_sensor_list_logged_in(client):
    with client:
        # login
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "test", "login": "login"},
        )
        # should get a redirect
        assert response.status_code == 302
        response = client.get("/sensors/sensor_list")
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        # check the title
        assert "<title>CROP |  SENSORS </title>" in html_content
        # check we have a table
        assert '<table id="datatable-responsive"' in html_content
        # should have 15 rows
        assert html_content.count("<tr class='clickable-row' method = POST>") == 15


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_sensor_form_not_logged_in(client):
    response = client.get("/sensors/sensor_form")
    assert response.status_code == 401


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_sensor_form_logged_in(client):
    with client:
        # login
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "test", "login": "login"},
        )
        # should get a redirect
        assert response.status_code == 302
        response = client.get("/sensors/sensor_form")
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        # check the title
        assert "<title>CROP |  EDIT SENSOR </title>" in html_content
        # check we have some expected headings
        assert "<h4>Choose sensor to edit:</h4>" in html_content
        assert "<h4>Create a new sensor:</h4>" in html_content
