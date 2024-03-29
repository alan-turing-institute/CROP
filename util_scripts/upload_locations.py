"""
Utility script to upload to the "location" table in the database.
"""

import logging
import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from cropcore.structure import LocationClass
from cropcore.utils import get_crop_db_session

TUNNEL_AISLES_DICT = {
    "Tunnel3": ["A", "B"],
    "Tunnel4": ["E"],
    "Tunnel5": ["C"],
    "Tunnel6": ["D"],
}

AISLES_COLUMNS_DICT = {"A": 32, "B": 32, "C": 24, "D": 16, "E": 12}
NUM_SHELVES = 4


def add_locations(tunnel_dict, aisle_dict, num_shelves):
    session = get_crop_db_session()
    rows = []
    for tunnel, aisles in tunnel_dict.items():
        for aisle in aisles:
            for column in range(1, aisle_dict[aisle] + 1):
                for shelf in range(1, num_shelves + 1):
                    row = {
                        "zone": tunnel,
                        "aisle": aisle,
                        "column": column,
                        "shelf": shelf,
                    }
                    print(f"uploading location {tunnel}")
                    location = LocationClass(
                        zone=tunnel, aisle=aisle, column=column, shelf=shelf
                    )
                    try:
                        session.add(location)
                        session.commit()
                    except:
                        session.rollback()

                    rows.append(row)
    df = pd.DataFrame(rows)
    session.close()
    return df


if __name__ == "__main__":
    df = add_locations(TUNNEL_AISLES_DICT, AISLES_COLUMNS_DICT, NUM_SHELVES)
