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
from __app__.crop.ingress_hyper import (
    get_api_sensor_data,
    CONST_CHECK_URL_PATH,
    READINGS_DICTS
)

DUMMY_API_KEY = "dummy"
THIS_DIR = os.path.dirname(os.path.realpath(__file__))
MOCK_TRH_DATA = json.load(open(os.path.join(THIS_DIR,"data","Hyper","hyper_trh_testdata.json")))
MOCK_CO2_DATA = json.load(open(os.path.join(THIS_DIR,"data","Hyper","hyper_co2_testdata.json")))
MOCK_AIRVELOCITY_DATA = json.load(open(os.path.join(THIS_DIR,"data","Hyper","hyper_airvelocity_testdata.json")))

DT_FROM = datetime.utcnow() + timedelta(days=-1)
DT_TO = datetime.utcnow()


def test_get_trh_api_data():

    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json=MOCK_TRH_DATA)
        success, error, dfs = get_api_sensor_data(
            DUMMY_API_KEY,
            DT_FROM,
            DT_TO,
            READINGS_DICTS[0]["columns"]
        )
        assert success
        assert isinstance(dfs, dict)
        for k,v in dfs.items():
            assert isinstance(k, str)
            assert isinstance(v, pd.DataFrame)
            assert len(v) > 0
            assert "Temperature" in v.columns
            assert "Humidity" in v.columns


def test_get_co2_api_data():

    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json=MOCK_CO2_DATA)
        success, error, dfs = get_api_sensor_data(
            DUMMY_API_KEY,
            DT_FROM,
            DT_TO,
            READINGS_DICTS[1]["columns"]
        )
        assert success
        assert isinstance(dfs, dict)
        for k,v in dfs.items():
            assert isinstance(k, str)
            assert isinstance(v, pd.DataFrame)
            assert len(v) > 0
            assert "CO2" in v.columns


def test_get_airvelocity_api_data():

    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json=MOCK_AIRVELOCITY_DATA)
        success, error, dfs = get_api_sensor_data(
            DUMMY_API_KEY,
            DT_FROM,
            DT_TO,
            READINGS_DICTS[2]["columns"]
        )
        assert success
        assert isinstance(dfs, dict)
        for k,v in dfs.items():
            assert isinstance(k, str)
            assert isinstance(v, pd.DataFrame)
            assert len(v) > 0
            assert "Current" in v.columns
            assert "CurrentDerived" in v.columns
