import os
import pandas as pd
from pathlib import Path

from cropcore.db import connect_db, session_open, session_close
from cropcore.constants import SQL_CONNECTION_STRING, SQL_DBNAME

from cropcore.structure import (
    ModelClass,
    ModelMeasureClass,
    ModelScenarioClass,
)

# Relative import doesn't work if we are in same dir as this module
if os.getcwd() == os.path.dirname(os.path.realpath(__file__)):
    from config import config
else:
    from .config import config


def get_sqlalchemy_session(connection_string=None, dbname=None):
    if not connection_string:
        connection_string = SQL_CONNECTION_STRING
    if not dbname:
        dbname = SQL_DBNAME
    status, log, engine = connect_db(connection_string, dbname)
    session = session_open(engine)
    return session


def get_ges_model_id(model_name="Greenhouse Energy Simulation (GES)", session=None):
    if not session:
        session = get_sqlalchemy_session()
    query = session.query(ModelClass.id, ModelClass.model_name).filter(
        ModelClass.model_name == model_name
    )
    result = session.execute(query).fetchone()
    if result:
        return result[0]
    return None


def get_scenarios_by_id(scenario_ids, session=None):
    """
    Take a list of scenario ids and produce a dataframe
    for each
    """
    if not session:
        session = get_sqlalchemy_session()
    df_all = pd.DataFrame(
        columns=[
            "ventilation_rate",
            "num_dehumidifiers",
            "lighting_shift",
            "lighting_on_duration",
        ]
    )
    dfs = []
    for scenario_id in scenario_ids:
        query = session.query(
            ModelScenarioClass.ventilation_rate,
            ModelScenarioClass.num_dehumidifiers,
            ModelScenarioClass.lighting_shift,
            ModelScenarioClass.lighting_on_duration,
        ).filter(
            ModelScenarioClass.id == scenario_id,
        )
        result = session.execute(query).fetchall()
        df = pd.DataFrame(
            result,
            columns=[
                "ventilation_rate",
                "num_dehumidifiers",
                "lighting_shift",
                "lighting_on_duration",
            ],
        )
        dfs.append(df)
    df_all = pd.concat(dfs)
    return df_all


def get_scenarios(model_name="Greenhouse Energy Simulation (GES)", session=None):
    if not session:
        session = get_sqlalchemy_session()
    query = session.query(
        ModelScenarioClass.ventilation_rate,
        ModelScenarioClass.num_dehumidifiers,
        ModelScenarioClass.lighting_shift,
        ModelScenarioClass.lighting_on_duration,
    ).filter(
        ModelScenarioClass.model_id == ModelClass.id,
        ModelClass.model_name == model_name,
    )
    result = session.execute(query).fetchall()
    df = pd.DataFrame(
        result,
        columns=[
            "ventilation_rate",
            "num_dehumidifiers",
            "lighting_shift",
            "lighting_on_duration",
        ],
    )
    return df


def get_measures(
    scenario_id=None, model_name="Greenhouse Energy Simulation (GES)", session=None
):
    if not session:
        session = get_sqlalchemy_session()
    query = session.query(
        ModelMeasureClass.measure_name,
        ModelMeasureClass.measure_description,
        ModelMeasureClass.scenario_id,
    ).filter(
        ModelMeasureClass.scenario_id == ModelScenarioClass.id,
        ModelScenarioClass.model_id == ModelClass.id,
        ModelClass.model_name == model_name,
    )
    if scenario_id:
        query = query.filter(ModelMeasureClass.scenario_id == scenario_id)
    result = session.execute(query).fetchall()
    df = pd.DataFrame(
        result, columns=["measure_name", "measure_description", "scenario_id"]
    )
    return df


def get_weather_data_from_file(data_dir=None):
    """
    Read the data csv file that was output from the first part of the calibration.
    """
    path_conf = config(section="paths")
    if not data_dir:
        data_dir = Path(path_conf["data_dir"])
    filepath = os.path.join(data_dir, path_conf["filename_weather"])
    header_list = ["DateTime", "T_e", "RH_e"]
    df = pd.read_csv(filepath, delimiter=",", names=header_list)
    df.set_index("DateTime", inplace=True)
    return df


def get_latest_time_hour_value(data_dir=None):
    """
    Get the latest hour from the weather csv.
    """
    df = get_weather_data_from_file(data_dir)
    latest_time = df[-1:]
    latest_time_hour_value = pd.DatetimeIndex(latest_time.index).hour.astype(float)[0]
    return latest_time_hour_value
