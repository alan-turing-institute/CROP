from flask import session
import pytest

# from conftest import client


def test_sensor_list_not_logged_in(client):
    response = client.get("/sensors/sensor_list")
    assert response.status_code == 401


def test_sensor_list_logged_in(client):
    with client:
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "pass", "login": "login"},
        )
        print(f"LOGGING IN {response.data}")
        #        response = client.get("/sensors/sensor_list")
        assert session["user_id"] == 1


#        assert response.status_code == 200
