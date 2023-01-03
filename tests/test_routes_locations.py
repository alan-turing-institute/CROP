"""
Test the routes defined in webapp/app/locations/routes.py
"""


# use the testuser fixture to add a user to the database
def test_user(testuser):
    assert True


def test_locations_not_logged_in(client):
    response = client.get("/locations/locations")
    assert response.status_code == 401


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


def test_location_form_not_logged_in(client):
    response = client.get("/locations/location_form")
    assert response.status_code == 401


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
