
"""
Module to import sensor data to a postgres database.
"""

from core.crop.db import connect_db

from core.crop.populate_db import session_open, session_close, insert_advanticsys_data

def import_data(pd_df, sensor_type, server, user, password, host, port, db_name):
    """
    This function will take the checked sensor data (pd_df)
    perform data checks and insert them into the db.
    -data: raw data from a sensor as a csv (or dataframe??)
    -sensor_type: type of sensor
    
    Parameters required to connect to the database:
    -server: PostgreSQL
    -user: my user name
    -password: my password
    -host: the host name of the server
    -port: the port number the server is listening on
    -db_name: my database name

    """

    connection_string = "%s://%s:%s@%s:%s" % (
        server,
        user,
        password,
        host,
        port
    )

    # Try to connect to a database that exists
    success, log, engine = connect_db(connection_string, db_name)
    if not success:
        return success, log

    # Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)
    
    if (sensor_type == "advanticsys"): # FIXME:(name or id?)
        # load advanticsys sensor data to db
        success, log = insert_advanticsys_data(session, pd_df)
        if not success:
            return success, log

    #TODO: add the other types
    else: pass

    session_close(session)

    return True, None
