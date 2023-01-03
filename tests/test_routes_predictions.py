"""
Test the routes that show results of predictive models
"""

# use the testuser fixture to add a user to the database
def test_user(testuser):
    assert True


def test_predictions_arima(client):
    # login
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "test", "login": "login"},
    )
    # should get a redirect
    assert response.status_code == 302
    response = client.get("/predictions/arima")
    assert response.status_code == 200
    html_content = response.data.decode("utf-8")
    # check title
    assert "<title>CROP |  ARIMA PREDICTIONS </title>" in html_content
    # check heading
    assert "Arima: Temperature predictions</h2>" in html_content
    # check we have some javascript that loops through sensors
    assert "function sensor_loop(data) {" in html_content


def test_predictions_ges(client):
    # login
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "test", "login": "login"},
    )
    # should get a redirect
    assert response.status_code == 302
    response = client.get("/predictions/ges")
    assert response.status_code == 200
    html_content = response.data.decode("utf-8")
    # check title
    assert "<title>CROP |  GES PREDICTIONS </title>" in html_content
    # check heading
    assert "GES: Temperature and humidity predictions</h2>" in html_content
    # check subheading
    assert '<h4> <p id="ges_model_title"></p></h4>' in html_content
