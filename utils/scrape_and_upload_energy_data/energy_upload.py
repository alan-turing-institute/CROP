"""
Scrape and upload stark energy data for the last 4 months

"""

from __app__.crop.ingress_energy import scrape_data, import_energy_data
from __app__.crop.constants import SQL_CONNECTION_STRING, SQL_DBNAME

if __name__ == "__main__":
    
    # Get the data from the website
    status, error, energy_df = scrape_data(hide=True, prev=4)

    if status:
        # upload data
        status, error = import_energy_data(
            energy_df, SQL_CONNECTION_STRING, SQL_DBNAME
        )

    print(status, error)
