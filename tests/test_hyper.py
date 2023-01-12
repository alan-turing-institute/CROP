"""
Test ingress_hyper.py module
"""
import os
import json
import re
from datetime import datetime, timedelta
import pandas as pd
import requests
import requests_mock
from core.ingress_hyper import get_api_sensor_data, READINGS_DICTS
from core.constants import CONST_TESTDATA_ENVIRONMENT_FOLDER


DUMMY_API_KEY = "dummy"
MOCK_TRH_DATA = json.load(
    open(os.path.join(CONST_TESTDATA_ENVIRONMENT_FOLDER, "hyper_trh_testdata.json"))
)
MOCK_CO2_DATA = json.load(
    open(os.path.join(CONST_TESTDATA_ENVIRONMENT_FOLDER, "hyper_co2_testdata.json"))
)
MOCK_AIRVELOCITY_DATA = json.load(
    open(
        os.path.join(
            CONST_TESTDATA_ENVIRONMENT_FOLDER, "hyper_airvelocity_testdata.json"
        )
    )
)
MOCK_IRRIGATION_DATA = json.load(
    open(
        os.path.join(
            CONST_TESTDATA_ENVIRONMENT_FOLDER, "hyper_irrigation_testdata.json"
        )
    )
)

DT_FROM = datetime.utcnow() + timedelta(days=-1)
DT_TO = datetime.utcnow()


def test_get_trh_api_data():

    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json=MOCK_TRH_DATA)
        success, error, dfs = get_api_sensor_data(
            DUMMY_API_KEY, DT_FROM, DT_TO, READINGS_DICTS[0]["columns"]
        )
        assert success
        assert isinstance(dfs, dict)
        for k, v in dfs.items():
            assert isinstance(k, str)
            assert isinstance(v, pd.DataFrame)
            assert len(v) > 0
            assert "Temperature" in v.columns
            assert "Humidity" in v.columns


def test_get_co2_api_data():

    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json=MOCK_CO2_DATA)
        success, error, dfs = get_api_sensor_data(
            DUMMY_API_KEY, DT_FROM, DT_TO, READINGS_DICTS[1]["columns"]
        )
        assert success
        assert isinstance(dfs, dict)
        for k, v in dfs.items():
            assert isinstance(k, str)
            assert isinstance(v, pd.DataFrame)
            assert len(v) > 0
            assert "CO2" in v.columns


def test_get_airvelocity_api_data():

    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json=MOCK_AIRVELOCITY_DATA)
        success, error, dfs = get_api_sensor_data(
            DUMMY_API_KEY, DT_FROM, DT_TO, READINGS_DICTS[2]["columns"]
        )
        assert success
        assert isinstance(dfs, dict)
        for k, v in dfs.items():
            assert isinstance(k, str)
            assert isinstance(v, pd.DataFrame)
            assert len(v) > 0
            assert "Current" in v.columns
            assert "CurrentDerived" in v.columns


def test_get_irrigation_api_data():

    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json=MOCK_IRRIGATION_DATA)
        success, error, dfs = get_api_sensor_data(
            DUMMY_API_KEY, DT_FROM, DT_TO, READINGS_DICTS[3]["columns"]
        )
        assert success
        assert isinstance(dfs, dict)
        for k, v in dfs.items():
            assert isinstance(k, str)
            assert isinstance(v, pd.DataFrame)
            assert len(v) > 0
            assert "WaterTemperature" in v.columns
            assert "WaterPH" in v.columns
            assert "WaterConductivity" in v.columns
            assert "WaterOxygen" in v.columns
            assert "WaterTurbidity" in v.columns
            assert "WaterPeroxide" in v.columns
