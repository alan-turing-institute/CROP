import pytest

from ..crop.create_db import create_database


def test_create_database():

    try:
        create_database(None)
    except:
        assert(False)

    assert(True)


# #import createdb
# import main

# #check if files are loaded in the dataframes
# def check(file):
#     try:
#         #main.Readings_Advantix ()
#         print ("itworked")
#     except AssertionError:
#         assert False, "  cant read csv"

# check(df)


