"""
Test the homepage renders OK
"""

import re
import pytest

from .conftest import check_for_docker

DOCKER_RUNNING = check_for_docker()

# use the testuser fixture to add a user to the database
@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_user(testuser):
    assert True


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_homepage_not_logged_in(client):
    # On some platforms, the message is a slightly different (the optional "the"), so we
    # use a regular expression to catch both cases.
    test_regex = re.compile(
        r"<title>Redirecting\.\.\.</title>\n"
        r"<h1>Redirecting\.\.\.</h1>\n"
        r"<p>You should be redirected automatically to (the )?target URL: "
        r'<a href="/login">/login</a>'
    )
    with client:
        response = client.get("/")
        # should redirect to login page
        assert response.status_code == 302
        html_content = response.data.decode("utf-8")
        assert test_regex.search(html_content) is not None


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_homepage_logged_in(client):
    # login
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "test", "login": "login"},
    )
    # should get a redirect
    assert response.status_code == 302
    response = client.get("/home/index")
    assert response.status_code == 200
    html_content = response.data.decode("utf-8")
    # check the title
    assert "<title>CROP |  INDEX </title>" in html_content
    # check we have sidebar
    assert '<div id="sidebar-menu"' in html_content
    # check we have link to the Unity model
    assert '<div id="unityContainer">' in html_content
    # check we have the donut charts
    assert '<canvas id="roundchart1" ></canvas>' in html_content
    # check we have the vertical stratification
    assert "<h2>Vertical stratification</h2>" in html_content
    assert '<canvas id="vertical_temp_stratification"></canvas>' in html_content
    # and horizontal stratification
    assert "<h2>Horizontal stratification</h2>" in html_content
    assert '<canvas id="horizontal_temp_stratification"></canvas>' in html_content
    # check we have the warnings section
    assert "<h2>Alerts <small></small></h2>" in html_content
