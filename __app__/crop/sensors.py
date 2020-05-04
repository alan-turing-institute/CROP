from __app__.crop.structure import TypeClass

def find_sensor_type_id(session, sensor_type):
    """
    Function to find sensor type id by name.

    Args:
        session: sqlalchemy activee seession object
        sensor_type: sensor type name

    Returns:
        type_id: type id, -1 if not found
        log: message if not found
    """

    type_id = -1
    log = ""

    # Gets the the assigned int id of sensor type

    try:
        type_id = (
            session.query(TypeClass)
            .filter(TypeClass.sensor_type == sensor_type)
            .first()
            .id
        )
    except:
        log = "Sensor type {} was not found.".format(sensor_type)

    return type_id, log