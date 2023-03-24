import os
import pandas as pd
from pathlib import Path

from cropcore.db import connect_db, session_open, session_close
from cropcore.constants import SQL_CONNECTION_STRING, SQL_DBNAME
from cropcore.model_data_access import get_sqlalchemy_session
from cropcore.structure import (
    ModelClass,
    ModelMeasureClass,
    ModelScenarioClass,
    ScenarioType,
)

# Relative import doesn't work if we are in same dir as this module
if os.getcwd() == os.path.dirname(os.path.realpath(__file__)):
    from config import config
else:
    from .config import config


def get_ges_model_id(model_name="Greenhouse Energy Simulation (GES)", session=None):
    """
    Find the index of the specified model in the database

    Parameters
    ----------
    model_name: str, name of e.g. GES model in the ModelClass table in the db.
    session: sqlalchemy session.  If None, use default db.

    Returns
    -------
    model_id: int, or None if not found
    """
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
    Take a scenario_id or list of scenario ids and produce a dataframe
    with one row for each.

    Parameters
    ----------
    scenario_ids: int, or list of ints, scenario_ids from the database
    session: sqlalchemy session.  If None, use default connection parameters.

    Returns
    -------
    df: pd.DataFrame, containing one scenario per row.
    """
    if not session:
        session = get_sqlalchemy_session()

    query = session.query(
        ModelScenarioClass.ventilation_rate,
        ModelScenarioClass.num_dehumidifiers,
        ModelScenarioClass.lighting_shift,
        ModelScenarioClass.lighting_on_duration,
        ModelScenarioClass.scenario_type,
    )
    if isinstance(scenario_ids, int):
        query = query.filter(ModelScenarioClass.id == scenario_ids)
    else:
        query = query.filter(ModelScenarioClass.id.in_(scenario_ids))
    result = session.execute(query).fetchall()
    df = pd.DataFrame(
        result,
        columns=[
            "ventilation_rate",
            "num_dehumidifiers",
            "lighting_shift",
            "lighting_on_duration",
            "scenario_type",
        ],
    )
    return df


def get_bau_scenario_id(model_name="Greenhouse Energy Simulation (GES)", session=None):
    """
    Find the scenario_id corresponding to the Business As Usual scenario.
    """
    print(f"Getting BAU scenario ID for model {model_name}")
    if not session:
        session = get_sqlalchemy_session()
    query = session.query(ModelScenarioClass.id,).filter(
        ModelScenarioClass.scenario_type == ScenarioType.BAU,
        ModelScenarioClass.model_id == ModelClass.id,
        ModelClass.model_name == model_name,
    )
    result = session.execute(query).fetchone()
    return result[0]


def get_scenarios(model_name="Greenhouse Energy Simulation (GES)", session=None):
    if not session:
        session = get_sqlalchemy_session()
    query = session.query(
        ModelScenarioClass.id,
        ModelScenarioClass.ventilation_rate,
        ModelScenarioClass.num_dehumidifiers,
        ModelScenarioClass.lighting_shift,
        ModelScenarioClass.lighting_on_duration,
        ModelScenarioClass.scenario_type,
    ).filter(
        ModelScenarioClass.model_id == ModelClass.id,
        ModelClass.model_name == model_name,
    )
    result = session.execute(query).fetchall()
    df = pd.DataFrame(
        result,
        columns=[
            "id",
            "ventilation_rate",
            "num_dehumidifiers",
            "lighting_shift",
            "lighting_on_duration",
            "scenario_type",
        ],
    )
    return df


def get_measures(
    scenario_ids=None, model_name="Greenhouse Energy Simulation (GES)", session=None
):
    """
    Get all 'measures' corresponding to selected model and scenario.

    Parameters
    ----------
    scenario_ids: int, list of ints, or None.   Either a single scenario_id, or a list
                 of them, or None to get all measures for a given model.
    model_name: str, the name of the model in the DB
    session: sqlalchemy session.  If None, use default db.

    Returns
    -------
    df: pd.DataFrame containing one Measure per row.
    """
    if not session:
        session = get_sqlalchemy_session()
    query = session.query(
        ModelMeasureClass.id,
        ModelMeasureClass.measure_name,
        ModelMeasureClass.measure_description,
        ModelMeasureClass.scenario_id,
    ).filter(
        ModelMeasureClass.scenario_id == ModelScenarioClass.id,
        ModelScenarioClass.model_id == ModelClass.id,
        ModelClass.model_name == model_name,
    )
    if scenario_ids and isinstance(scenario_ids, int):
        query = query.filter(ModelMeasureClass.scenario_id == scenario_ids)
    elif scenario_ids and isinstance(scenario_ids, list):
        query = query.filter(ModelMeasureClass.scenario_id.in_(scenario_ids))
    result = session.execute(query).fetchall()
    df = pd.DataFrame(
        result,
        columns=["measure_id", "measure_name", "measure_description", "scenario_id"],
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


def create_measures_dicts(
    scenario_ids=None, model_name="Greenhouse Energy Simulation (GES)", session=None
):
    """
    Given a list of scenario IDs, construct a list of dictionaries,
    one dictionary per Measure, to help the postprocessing and entry into the DB.

    Parameters
    ----------
    scenario_ids: list of ints, if None, use all scenarios.
    model_name: name in the DB of the Model to which the scenarios for the measures apply.
    session: sqlalchemy session.  If None, use default DB.

    Returns
    -------
    measure_list: list of dicts.  In each dict (one per measure), the following items:
          measure_database_id: int, the primary key of this measure in the DB
          result_index: int, this is where the value for this measure is found in the 2nd dim
                of the array returned by TestScenarioV1_1.runModel().  That array dimension will
                have size 2+n_scenarios, as
          preprocess: str, this will be 'to_celcius' for temperatures, and 'to_percent' for
                humidities, and will tell the pipelineV1_1.assemble_values() func how to process.
          result_key: str, this will be 'T_air' for temperatures, and 'RH_air' for humidities.
                It is used to get the correct array of results from the dict returned by runModel.
    """
    if not session:
        session = get_sqlalchemy_session()
    # we always want to get the "Business As Usual" scenario
    bau_scenario_id = get_bau_scenario_id(model_name=model_name, session=session)
    if isinstance(scenario_ids, list) and not bau_scenario_id in scenario_ids:
        scenario_ids = [bau_scenario_id] + scenario_ids
    measure_df = get_measures(
        scenario_ids=scenario_ids, model_name=model_name, session=session
    )
    measure_list = []
    for _, row in measure_df.iterrows():
        measure_dict = {
            "measure_database_id": row.measure_id,
        }
        if row.scenario_id == bau_scenario_id:
            if "Mean" in row.measure_name:
                measure_dict["result_index"] = 0
            elif "Upper Bound" in row.measure_name:
                measure_dict["result_index"] = 1
            elif "Lower Bound" in row.measure_name:
                measure_dict["result_index"] = 2
            else:
                raise RuntimeError(f"measure_name {row.measure_name} not recognized")
        else:
            # first non-BAU scenario will be 2, mean value will be in position index 3
            measure_dict["result_index"] = 1 + row.scenario_id
        if "Temperature" in row.measure_name:
            measure_dict["preprocess"] = "to_celcius"
            measure_dict["result_key"] = "T_air"
        elif "Relative Humidity" in row.measure_name:
            measure_dict["preprocess"] = "to_percent"
            measure_dict["result_key"] = "RH_air"
        else:
            raise RuntimeError(f"measure_name {row.measure_name} not recognized")
        measure_list.append(measure_dict)
    return measure_list
