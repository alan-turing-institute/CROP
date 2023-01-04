"""
Test the routes defined in webapp/app/locations/routes.py
"""
import pytest

from .conftest import check_for_docker

DOCKER_RUNNING = check_for_docker()

# use the testuser fixture to add a user to the database
@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_user(testuser):
    assert True


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_locations_not_logged_in(client):
    response = client.get("/locations/locations")
    assert response.status_code == 401


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_locations_logged_in(client):
    with client:
        # login
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "test", "login": "login"},
        )
        # should get a redirect
        assert response.status_code == 302
        response = client.get("/locations/locations")
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        # check the title
        assert "<title>CROP |  LOCATIONS </title>" in html_content
        # check we have a table
        assert '<table id="datatable-responsive"' in html_content
        # should have 12 rows
        assert html_content.count("<tr class='clickable-row' method = POST>") == 12


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_location_form_not_logged_in(client):
    response = client.get("/locations/location_form")
    assert response.status_code == 401


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_location_form_logged_in(client):
    with client:
        # login
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "test", "login": "login"},
        )
        # should get a redirect
        assert response.status_code == 302
        response = client.get("/locations/location_form")
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        # check the title
        assert "<title>CROP |  LOCATION FORM </title>" in html_content
        # check we have expected heading
        assert "<h3>Add location</h3>" in html_content
