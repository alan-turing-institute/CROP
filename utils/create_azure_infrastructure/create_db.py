#!/usr/bin/python
"""
Script to initialise CROP database.

"""

import sys

from crop.create_db import (
    create_database
)

from crop.constants import SQL_DBNAME

def confirm(question):
    """
    Ask user to enter Y or N (case-insensitive).
    :return: True if the answer is Y.

    """
    answer = ""

    while answer not in ["y", "n"]:
        answer = input("{0} [Y/N]? ".format(question)).lower()
    return answer == "y"

if __name__ == "__main__":

    if confirm("Create DB?"):
        create_database(SQL_DBNAME)

    print("Finished.")