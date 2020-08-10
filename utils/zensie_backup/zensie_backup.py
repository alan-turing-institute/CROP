"""

A script to backup 30 MHz sensor data using Zensie API.

The routine uses api key to connect to the ZENSIE API and iterates
through a list of sensors. Backed up data is saved into a
new folder as separate compressed (zip) csv files for each sensor.
"""

import copy
import os
import argparse
from datetime import datetime, timezone, timedelta

import yaml
import requests
import pandas as pd

CONST_CONFIG_FILE = "config.yml"
CONST_CHECK_URL_PATH = "https://api.30mhz.com/api/stats/check"
CONST_CHECK_PARAMS = "statisticType=averages&intervalSize=5m"
CONST_TIME_PRINT_FORMAT = "%Y-%m-%d %H:%M:%S"
CONST_TIME_FILE_FORMAT = "%Y-%m-%d-%H-%M-%S"


def log(message, indent=0):
    """
    Log function.
    Arguments:
        message: log message
        indent: indentation level
    """

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    indent_str = ""
    for _ in range(indent):
        indent_str += "  "

    print("%s | %s%s" % (utc_timestamp, indent_str, message))


def forward_date_range(start_dt, end_dt, span_days):
    """
    Generate tuples with intervals from given range of dates (forward).

    Arguments:
        start_dt
        end_dt
        span_days
    Returns:
        Tuples with date ranges
    """

    span = timedelta(days=span_days)
    step = timedelta(days=1)

    while start_dt + span < end_dt:
        current = start_dt + span
        yield start_dt, current
        start_dt = current + step
    else:
        yield start_dt, end_dt


def get_api_sensor_data(api_key, check_id, dt_from, dt_to):
    """
    Makes a request to download sensor data for a specified period of time.

    Arguments:
        api_key: api key for authetication
        check_id: sensor identifier
        dt_from: date range from
        dt_to: date range to
    Return:
        success: whether data request was succesful
        error: error message
        data_df: sensor data as pandas dataframe
    """

    log(
        "Download period: %s - %s"
        % (
            dt_from.strftime(CONST_TIME_PRINT_FORMAT),
            dt_to.strftime(CONST_TIME_PRINT_FORMAT),
        ),
        indent=4,
    )

    success = True
    error = ""
    data_df = None

    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key,
    }

    dt_from_iso = dt_from.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    dt_to_iso = dt_to.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    url = "{}/{}/from/{}/until/{}?{}".format(
        CONST_CHECK_URL_PATH, check_id, dt_from_iso, dt_to_iso, CONST_CHECK_PARAMS
    )

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data_df = pd.read_json(response.content).T

        if data_df.empty:
            error = "Request [%s]: no data" % (url[: min(70, len(url))])
            success = False

    else:
        error = "Request's [%s] status code: %d" % (
            url[: min(70, len(url))],
            response.status_code,
        )
        success = False

    if success:
        data_df.reset_index(inplace=True, drop=False)
        data_df.rename(columns={"index": "Timestamp"}, inplace=True)

    return success, error, data_df


def backup_sensor_data(api_key, sensors_dict, dt_from, dt_to):
    """
    The main routine to backup 30 MHz sensor data using Zensie API.
        The routine uses apikey to connect to the ZENSIE API and iterates through the list
        of sensors given as a dictionary. If the data backup date range period is longer
        than 7 days, zensie api might complain, thus we split the date range into 7 days
        intervals. Backed up data is saved into a new folder as a separate compressed
        (zip) csv file for each sensor.

    Arguments:
        api_key: api key for authetication
        check_id: sensor identifier
        dt_from: date range from
        dt_to: date range to
    """

    cwd = os.getcwd()

    backup_dir_name = "Zensie_Backup_%s" % datetime.now().strftime(
        CONST_TIME_FILE_FORMAT
    )

    log("Creating backup directory %s" % (backup_dir_name), indent=0)

    os.mkdir(backup_dir_name)
    os.chdir(backup_dir_name)

    for sensor_dict in sensors_dict:
        sensor_name = list(sensor_dict.keys())[0]
        sensor_checkid = sensor_dict[sensor_name]

        log("Downloading data for %s (%s)" % (sensor_name, sensor_checkid), indent=2)

        data_df = None
        if (dt_to - dt_from).days > 7:
            for dt_from_i, dt_to_i in forward_date_range(dt_from, dt_to, 7):

                success, error, data_df_i = get_api_sensor_data(
                    api_key, sensor_checkid, dt_from_i, dt_to_i
                )
                log("Download status: %r - %s" % (success, error), indent=6)

                if success:
                    if data_df is None:
                        data_df = copy.copy(data_df_i)
                    else:
                        data_df = data_df.append(data_df_i, ignore_index=True)

        else:
            success, error, data_df = get_api_sensor_data(
                api_key, sensor_checkid, dt_from, dt_to
            )
            log("Download status: %r - %s" % (success, error), indent=6)

        if data_df is not None:
            sensor_name_no_special = sensor_name.translate(
                {ord(c): "_" for c in "\!@#$%^&*()[]{};:,./><?|`~-=+'"}
            )

            filename = "%s_%s_%s" % (
                sensor_name_no_special,
                dt_from.strftime(CONST_TIME_FILE_FORMAT),
                dt_to.strftime(CONST_TIME_FILE_FORMAT),
            )

            zip_filename = "%s.zip" % (filename)

            data_df.to_csv(
                zip_filename,
                index=False,
                compression=dict(method="zip", archive_name="%s.csv" % (filename)),
            )

            log("Saving data into: %s" % (zip_filename), indent=4)

    os.chdir(cwd)


def main(args):
    """
    Main backup function.

    Arguments:
        args - command line arguments

    """

    log("Reading config file %s" % (args.fconfig))

    with open(args.fconfig, "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    dt_to = datetime.now()

    dt_from = dt_to + timedelta(days=-5)

    zensie_apikey = cfg["zensie_apikey"]
    sensors_dict = cfg["sensors"]

    backup_sensor_data(zensie_apikey, sensors_dict, dt_from, dt_to)


if __name__ == "__main__":

    # Command line arguments
    PARSER = argparse.ArgumentParser(
        description="Backs up 30MHz Sensor Data using Zensie API."
    )

    PARSER.add_argument(
        "--dfrom",
        type=datetime.fromisoformat,
        help="Backup period start date, e.g. 2020-08-01 (default: today - 30 days).",
    )

    PARSER.add_argument(
        "--dto",
        type=datetime.fromisoformat,
        help="Backup period end date, e.g. 2020-08-20 (default: today).",
    )

    PARSER.add_argument(
        "--fconfig",
        default=CONST_CONFIG_FILE,
        help="YAML config file (default: %s)." % (CONST_CONFIG_FILE),
    )

    ARGS, _ = PARSER.parse_known_args()

    log("Started")

    main(ARGS)

    log("Finished")
