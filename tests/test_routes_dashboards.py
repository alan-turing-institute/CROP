"""
Test the routes that show dashboards
"""

import pytest

from .conftest import check_for_docker

DOCKER_RUNNING = check_for_docker()

# use the testuser fixture to add a user to the database
@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_user(testuser):
    assert True


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_dashboard_trh(client):
    # login
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "test", "login": "login"},
    )
    # should get a redirect
    assert response.status_code == 302
    response = client.get("/dashboards/aranet_trh_dashboard")
    assert response.status_code == 200
    html_content = response.data.decode("utf-8")
    # check title
    assert (
        "<title>CROP |  Aranet T&RH Sensors Analysis Dashboard </title>" in html_content
    )
    # check heading
    assert "<h2>Aranet T&RH Sensors Temperature Range Counts</h2>" in html_content
    # check we have at least one plot div
    assert '<div class="plotDiv"' in html_content


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_dashboard_energy(client):
    # login
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "test", "login": "login"},
    )
    # should get a redirect
    assert response.status_code == 302
    response = client.get("/dashboards/energy_dashboard")
    assert response.status_code == 200
    html_content = response.data.decode("utf-8")
    # check title
    assert "<title>CROP |  Energy Usage Analysis Dashboard </title>" in html_content
    # check headings
    assert "<h3>Lights" in html_content
    assert "<h3>Ventilation" in html_content
    # check code for plotting lights-on and ventilation
    assert "Plotly.newPlot('plotLightsOnDiv', data, layout);" in html_content
    assert "Plotly.newPlot('plotVentilationDiv', data, layout);" in html_content


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_dashboard_timeseries(client):
    # login
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "test", "login": "login"},
    )
    # should get a redirect
    assert response.status_code == 302
    response = client.get("/dashboards/timeseries_dashboard")
    assert response.status_code == 200
    html_content = response.data.decode("utf-8")
    # check title
    assert "<title>CROP |  Timeseries Dashboard </title>" in html_content
    # check headings
    assert "<h3>Choose sensors and time period</h3>" in html_content
    # check we have at least one sensor checkbox
    assert '<div class="checkbox-inline" id="sensorCheckbox">' in html_content
    # check we have "plot" and "download" buttons
    assert (
        '<button style="margin-top: 5px" type="button" onclick="requestTimeSeries(false)">Plot</button>'
        in html_content
    )
    assert (
        '<button style="margin-top: 5px" type="button" onclick="requestTimeSeries(true)">Download</button>'
        in html_content
    )
