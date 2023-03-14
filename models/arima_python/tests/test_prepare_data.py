import arima.prepare_data as prepare_data
from datetime import datetime

prepare_data.arima_config["farm_cycle_start"] = "16h0m0s"


def test_standardize_timestamp():
    """
    Given a list of input timestamps, test whether the
    function `prepare_data.standardize_timestamp` outputs
    the expected standardized timestamps.
    """
    # list of input timestamps
    input_timestamps = ["2022-12-16 01:00:00"]
    input_timestamps.append("2022-12-16 11:00:00")
    input_timestamps.append("2022-12-16 16:00:00")
    input_timestamps.append("2022-12-17 07:00:00")
    input_timestamps.append("2022-12-17 15:00:00")
    input_timestamps.append("2022-12-16 00:00:00")
    input_timestamps.append("2022-12-15 22:00:00")
    # expected output timestamps when `farm_cycle_start`
    # in config.ini is set to "16h0m0s", as produced by
    # the original R code.
    expect_output_timestamps = ["2022-12-15 16:00:00"]
    expect_output_timestamps.append("2022-12-16 04:00:00")
    expect_output_timestamps.append("2022-12-16 16:00:00")
    expect_output_timestamps.append("2022-12-17 04:00:00")
    expect_output_timestamps.append("2022-12-17 04:00:00")
    expect_output_timestamps.append("2022-12-15 16:00:00")
    expect_output_timestamps.append("2022-12-15 16:00:00")

    for ii in range(len(input_timestamps)):
        # first, parse the strings into datetime objects
        timestamp = datetime.strptime(input_timestamps[ii], "%Y-%m-%d %H:%M:%S")
        output_timestamp = prepare_data.standardize_timestamp(timestamp)
        # convert datetime objects to strings
        output_timestamp = datetime.strftime(output_timestamp, "%Y-%m-%d %H:%M:%S")
        assert output_timestamp == expect_output_timestamps[ii]
