import pytest

from ..crop.constants import (
    SQL_DBNAME
)

from ..crop.create_db import (
    create_database
)

def test_create_database():

    try:
        create_database(SQL_DBNAME)
    except:
        assert(False)

    assert(True)

