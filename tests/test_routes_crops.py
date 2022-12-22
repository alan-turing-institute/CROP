"""
Test the routes defined in webapp/app/crops/routes.py
"""

# use the testuser fixture to add a user to the database
def test_user(testuser):
    assert True


def test_batch_list(client):
    with client:
        # login
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "test", "login": "login"},
        )
        # should get a redirect
        assert response.status_code == 302
        response = client.get("/crops/batch_list")
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "<title>CROP |  CROP BATCHES </title>" in html_content
        assert "<h3>Crop batches</h3>" in html_content
        # check we have a table
        assert '<table id="datatable-responsive"' in html_content
        # check we have a download button
        assert '<input type="submit" value="Download" name="download"/>' in html_content


def test_batch_details(client):
    with client:
        # login
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "test", "login": "login"},
        )
        # should get a redirect
        assert response.status_code == 302
        response = client.get("/crops/batch_details?query=1")
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")

        assert "<title>CROP |  CROP BATCH DETAILS </title>" in html_content
        # check we have a table
        assert '<table class="table table-borderless">' in html_content
        assert '<td class="text-alignright">Batch ID</td>' in html_content


def test_harvest_list(client):
    with client:
        # login
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "test", "login": "login"},
        )
        # should get a redirect
        assert response.status_code == 302
        response = client.get("/crops/harvest_list")
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        # check we have a table
        assert '<table id="datatable-responsive"' in html_content
        # check a few column headings
        assert "<th>Details</th>" in html_content
        assert "<th>Harvest time</th>" in html_content
        assert "<th>Unit yield (g/sqm)</th>" in html_content


def test_parallel_axes(client):
    with client:
        # login
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "test", "login": "login"},
        )
        # should get a redirect
        assert response.status_code == 302
        response = client.get("/crops/parallel_axes")
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        # check we have expected header
        assert "<h3>Yield visualisation</h3>" in html_content
        # check we have the crop type selector
        assert 'id="cropTypeSelector"' in html_content
        # check we have the checkboxes
        assert (
            '<div class="checkbox-inline" id="columnCheckboxyield_per_sqm">'
            in html_content
        )
        # check we have the colour picker
        assert 'id="colourAxisSelector"' in html_content
        # check we have the div for the plot itself
        assert '<div id="parallelAxesPlotDiv"></div>' in html_content
