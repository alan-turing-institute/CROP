'''
Unittest module for the database module.
'''

import pytest

from ..crop.database import (
    connect_to_db,
    disconnect_from_db
)


def test_connect_disconnect():
    """
    Tries to connect and disconnect to/from SQL server.
    """

    try:
        disconnect_from_db(connect_to_db())
    except:
        assert(False)

    assert(True)
