"""
Script to scrape stark.co.uk website for electricity usage data.
"""

from __app__.crop.ingress_energy import scrape_data


def main():
    """
    The main routine.
    """

    # Get the data from the website
    status, error, energy_df = scrape_data(hide=False)

    print("status: ", status)
    print("error: ", error)
    print("energy_df: ", energy_df)


if __name__ == "__main__":

    main()

    print("Finished.")
