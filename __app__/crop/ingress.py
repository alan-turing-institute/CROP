"""
Module to import sensor data to a postgres database.
"""

from __app__.crop.db import connect_db, session_open, session_close

from __app__.crop.ingress_adv import insert_advanticsys_data

from __app__.crop.constants import (
    CONST_ADVANTICSYS,
    SQL_ENGINE,
    SQL_DBNAME,
)

from __app__.crop.utils import make_conn_string
from __app__.crop.structure import DataUploadLogClass
from __app__.crop.sensors import find_sensor_type_id


def import_data(pd_df, sensor_type, user, password, host, port, db_name):
    """
    This function will take the checked sensor data (pd_df)
    perform data checks and insert them into the db.
    -data: raw data from a sensor as a csv (or dataframe??)
    -sensor_type: type of sensor

    Parameters required to connect to the database:
    -user: my user name
    -password: my password
    -host: the host name of the server
    -port: the port number the server is listening on
    -db_name: my database name

    """

    connection_string = make_conn_string(SQL_ENGINE, user, password, host, port)

    # Try to connect to a database that exists
    success, log, engine = connect_db(connection_string, db_name)
    if not success:
        return success, log

    # Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)

    if sensor_type == CONST_ADVANTICSYS:
        # load advanticsys sensor data to db
        success, log = insert_advanticsys_data(session, pd_df)
        if not success:
            return success, log

    # TODO: add the other types
    else:
        return False, "Sensor type des not exist"

    session_close(session)

    return True, log


def log_upload_event(sensor_type, filename, status, log, connection_string):
    """
    Function will log the upload event in the database by capturing information
        suchas sensor_type, time(now), filename, status, log message.

    - sensor_type: the type of sensor(s) for which the data is being uploaded
    - filename: the name of the file uploaded
    - status: boolean
    - log: log message from the upload routine
    - connection_string: connecetion string to the database

    """

    # Try to connect to a database that exists
    success, error, engine = connect_db(connection_string, SQL_DBNAME)

    if not success:
        return success, error

    # Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)

    type_id, error = find_sensor_type_id(session, sensor_type)

    success = type_id > -1

    if not success:
        return success, error

    if status:
        status_msg = "OK"
    else:
        status_msg = "FAILED"

    event_log = DataUploadLogClass(type_id, filename, status_msg, log)

    session.add(event_log)

    session_close(session)

    return success, error
