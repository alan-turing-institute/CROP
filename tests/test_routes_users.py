"""
Test the routes defined in webapp/app/users/routes.py
"""


# use the testuser fixture to add a user to the database
def test_user(testuser):
    assert True


def test_users_not_logged_in(client):
    response = client.get("/users/users")
    assert response.status_code == 401


def test_users_logged_in(client):
    with client:
        # login
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "test", "login": "login"},
        )
        # should get a redirect
        assert response.status_code == 302
        response = client.get("/users/users")
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        # check the title
        assert "<title>CROP |  USERS </title>" in html_content
        # check we have a table
        assert '<table id="datatable-responsive"' in html_content


def test_create_user_form_not_logged_in(client):
    response = client.get("/users/create_user_form")
    assert response.status_code == 401


def test_create_user_form_logged_in(client):
    with client:
        # login
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "test", "login": "login"},
        )
        # should get a redirect
        assert response.status_code == 302
        response = client.get("/users/create_user_form")
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        # check the title
        print(f"USERS {html_content}")
        # check we have expected heading
        assert "<h3>Create user</h3>" in html_content
