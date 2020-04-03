"""
Module to import sensor data to a postgres database.
"""

from __app__.crop.db import connect_db, session_open, session_close
from __app__.crop.ingress_adv import insert_advanticsys_data
from __app__.crop.constants import SQL_ENGINE, CONST_ADVANTICSYS

def import_data(pd_df, sensor_type, user, password, host, port, db_name):
    """

    """

    connection_string = "%s://%s:%s@%s:%s" % (SQL_ENGINE, user, password, host, port)

    # Try to connect to a database that exists
    success, log, engine = connect_db(connection_string, db_name)
    if not success:
        return success, log

    # Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)

    if sensor_type == CONST_ADVANTICSYS:
        # load advanticsys sensor data to db
        try:
            success, log = insert_advanticsys_data(session, pd_df)
        except:
            success = False
            log = "Error while performing insert_advanticsys_data."

        if not success:
            session_close(session)

            return success, log

    # TODO: add the other types
    else:
        pass

    session_close(session)

    return True, None
