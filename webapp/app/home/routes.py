"""
Analysis dashboards module.
"""

from datetime import timedelta

import numpy as np
import pandas as pd

from flask_login import login_required
from flask import render_template, request
from sqlalchemy import and_

from app.home import blueprint

from utilities.utils import parse_date_range_argument

from __app__.crop.structure import SQLA as db
from __app__.crop.structure import (
    SensorClass,
    ReadingsAdvanticsysClass,
    ReadingsEnergyClass,
)
from __app__.crop.constants import CONST_MAX_RECORDS


# Temperature constants
TEMP_BINS = [0, 17, 21, 24, 30]

# Ventilation constants
CONST_SFP = 2.39  # specific fan power
CONST_VTOT = 20337.0  # total volume – m3


def resample(df, bins, dt_from, dt_to):
    """
    Resamples (adds missing date/temperature bin combinations) to a dataframe.

    Arguments:
        df: dataframe with temperature assign to bins
        bins: temperature bins as a list
        dt_from: date range from
        dt_to: date range to
    Returns:
        bins_list: a list of temperature bins
        df_list: a list of df corresponding to temperature bins
    """

    bins_list = []
    for i in range(len(bins) - 1):
        bins_list.append("(%d, %d]" % (bins[i], bins[i + 1]))

    date_min = min(df["date"].min(), dt_from)
    date_max = max(df["date"].max(), dt_to)

    for n in range(int((date_max - date_min).days) + 1):
        day = date_min + timedelta(n)

        for temp_range in bins_list:
            if len(df[(df["date"] == day) & (df["temp_bin"] == temp_range)].index) == 0:

                df2 = pd.DataFrame(
                    {"date": [day], "temp_bin": [temp_range], "temp_cnt": [0]}
                )

                df = df.append(df2)

    df = df.sort_values(by=["date", "temp_bin"], ascending=True)

    df.reset_index(inplace=True, drop=True)

    df_list = []

    for bin_range in bins_list:

        df_bin = df[df["temp_bin"] == bin_range]

        del df_bin["temp_bin"]

        df_bin.reset_index(inplace=True, drop=True)

        df_list.append(df_bin)

    return bins_list, df_list


def lights_energy_use(dt_from_, dt_to_):
    """
    Energy use from Carpenter's place (with lights - called Clapham in the database)

    Arguments:
        dt_from_: date range from
        dt_to_: date range to
    Returns:
        lights_results_df - a pandas dataframe with mean lights on values
    """

    dt_from = pd.to_datetime(dt_from_.date()) + timedelta(hours=14)
    dt_to = pd.to_datetime(dt_to_.date()) + timedelta(days=1, hours=15)

    d_from = pd.to_datetime(dt_from_.date())
    d_to = pd.to_datetime(dt_to_.date())

    col_ec = "electricity_consumption"
    sensor_device_id = "Clapham"
    lights_on_cols = []

    lights_results_df = None

    # getting eneregy data for the analysis
    query = db.session.query(
        ReadingsEnergyClass.timestamp, ReadingsEnergyClass.electricity_consumption,
    ).filter(
        and_(
            SensorClass.device_id == sensor_device_id,
            ReadingsEnergyClass.sensor_id == SensorClass.id,
            ReadingsEnergyClass.timestamp >= dt_from,
            ReadingsEnergyClass.timestamp <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    if not df.empty:

        # Reseting index
        df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

        # grouping data by date-hour
        energy_hour = (
            df.groupby(
                by=[
                    df["timestamp"].map(
                        lambda x: pd.to_datetime(
                            "%04d-%02d-%02d-%02d" % (x.year, x.month, x.day, x.hour),
                            format="%Y-%m-%d-%H",
                        )
                    ),
                ]
            )["electricity_consumption"]
            .sum()
            .reset_index()
        )

        # Sorting and reseting index
        energy_hour.sort_values(by=["timestamp"], ascending=True).reset_index(
            inplace=True
        )

        # energy dates. Energy date starts from 4pm each day and lasts for 24 hours
        energy_hour.loc[
            energy_hour["timestamp"].dt.hour < 15, "energy_date"
        ] = pd.to_datetime((energy_hour["timestamp"] + timedelta(days=-1)).dt.date)
        energy_hour.loc[
            energy_hour["timestamp"].dt.hour >= 15, "energy_date"
        ] = pd.to_datetime(energy_hour["timestamp"].dt.date)

        # Clasification of lights being on

        # Lights ON 1: Lights turn on at 4pm and turn off at 9am, as scheduled.
        energy_hour["lights_on_1"] = energy_hour["timestamp"].apply(
            lambda x: 1 if (x.hour >= 17 or x.hour < 10) else 0
        )
        lights_on_cols.append("lights_on_1")

        # Lights ON 2: Lights are calculated by estimating the lighting use as between
        #   the minima of two consecutive days. The lights are considered on when the
        #   energy use is above the day's first quartile of lighting of this difference.
        # energy_hour['lights_on_2'] = 0
        # lights_on_cols.append('lights_on_2')

        # Lights ON 3: Lights are assumed to be on if the energy demand is over 30 kW
        #   (max load of the extraction fan)
        energy_hour["lights_on_3"] = energy_hour[col_ec].apply(
            lambda x: 1 if (x > 30.0) else 0
        )
        lights_on_cols.append("lights_on_3")

        # Lights ON 4: Lights are assumed to turn on at the time of largest energy use
        #   increase in the day, and turn off at the time of largest energy decrease of
        #   the day.

        # estimating energy difference
        energy_hour["dE"] = energy_hour[col_ec] - energy_hour[col_ec].shift(1)
        energy_hour["dE"] = energy_hour["dE"].fillna(0.0)

        # finding max increase and min decrease
        energy_hour["dE_min"] = energy_hour.groupby("energy_date")["dE"].transform(
            "min"
        )
        energy_hour["dE_max"] = energy_hour.groupby("energy_date")["dE"].transform(
            "max"
        )

        energy_hour.loc[
            np.isclose(energy_hour["dE_max"], energy_hour["dE"]), "lights_on_4"
        ] = 1
        energy_hour.loc[
            np.isclose(energy_hour["dE_min"], energy_hour["dE"]), "lights_on_4"
        ] = 0

        # repeat last?
        prev_row_value = None
        for df_index in energy_hour.index:
            if df_index > 0:
                if (np.isnan(energy_hour.loc[df_index, "lights_on_4"]) and \
                    not np.isnan(prev_row_value)):

                    energy_hour.loc[df_index, "lights_on_4"] = prev_row_value
            prev_row_value = energy_hour.loc[df_index, "lights_on_4"]

        lights_on_cols.append("lights_on_4")

        # Lights ON 5: Lights are assumed on if the energy use is over 0.9
        #   times the days' energy use mean, and the energy demand is over 30 kW.

        energy_hour["energy_date_mean"] = energy_hour.groupby("energy_date")[
            col_ec
        ].transform("mean")

        energy_hour["lights_on_5"] = np.where(
            (energy_hour[col_ec] > 30.0)
            & (energy_hour[col_ec] > 0.9 * energy_hour["energy_date_mean"]),
            1,
            0,
        )

        lights_on_cols.append("lights_on_5")

        # getting the mean value of lights on per day
        energy_date_df = energy_hour.loc[
            (energy_hour["energy_date"] >= d_from)
            & (energy_hour["energy_date"] <= d_to)
        ]
        energy_date_df = (
            energy_date_df.groupby(by=["energy_date"])[lights_on_cols]
            .sum()
            .reset_index()
        )
        energy_date_df["mean_lights_on"] = energy_date_df[lights_on_cols].sum(
            axis=1
        ) / len(lights_on_cols)
        energy_date_df["date"] = energy_date_df["energy_date"].dt.strftime("%Y-%m-%d")

        lights_results_df = energy_date_df[["date", "mean_lights_on"]]

    return lights_results_df


def ventilation_energy_use(dt_from, dt_to):
    """
    In our data this is called Carpenter’s Place. This reading only counts energy use for
        the second extraction fan.

    Arguments:
        dt_from: date range from
        dt_to: date range to
    Returns:
        ventilation_results_df - a pandas dataframe with ventilation analysis results
    """

    ventilation_results_df = None

    sensor_device_id = "1a Carpenters Place"

    # getting eneregy data for the analysis
    query = db.session.query(
        ReadingsEnergyClass.timestamp, ReadingsEnergyClass.electricity_consumption,
    ).filter(
        and_(
            SensorClass.device_id == sensor_device_id,
            ReadingsEnergyClass.sensor_id == SensorClass.id,
            ReadingsEnergyClass.timestamp >= dt_from,
            ReadingsEnergyClass.timestamp <= dt_to,
        )
    )

    df = pd.read_sql(query.statement, query.session.bind)

    if not df.empty:

        # Reseting index
        df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

        # grouping data by date-hour
        energy_hour = (
            df.groupby(
                by=[
                    df["timestamp"].map(
                        lambda x: "%04d-%02d-%02d %02d:00"
                        % (x.year, x.month, x.day, x.hour)
                    ),
                ]
            )["electricity_consumption"]
            .sum()
            .reset_index()
        )

        # Sorting and reseting index
        energy_hour.sort_values(by=["timestamp"], ascending=True).reset_index(
            inplace=True
        )

        # Calculating air exchange per hour
        energy_hour["ach"] = (
            energy_hour["electricity_consumption"]
            / CONST_SFP
            * 3600.0
            / (CONST_VTOT / 2.0)
        )

        ventilation_results_df = energy_hour[["timestamp", "ach"]]

    return ventilation_results_df


@blueprint.route("/index")
@login_required
def index():
    """
    Index page
    """
    return render_template("index.html")


@blueprint.route("/<template>")
@login_required
def route_template(template):
    """
    Renders templates
    """

    if template == "temperature":
        adv_sensors_temp = {}

        dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

        # advanticsys
        query = db.session.query(
            ReadingsAdvanticsysClass.timestamp,
            ReadingsAdvanticsysClass.sensor_id,
            SensorClass.id,
            ReadingsAdvanticsysClass.temperature,
            ReadingsAdvanticsysClass.humidity,
            ReadingsAdvanticsysClass.co2,
        ).filter(
            and_(
                ReadingsAdvanticsysClass.sensor_id == SensorClass.id,
                ReadingsAdvanticsysClass.timestamp >= dt_from,
                ReadingsAdvanticsysClass.timestamp <= dt_to,
            )
        )

        df = pd.read_sql(query.statement, query.session.bind)

        if not df.empty:

            # unique sensors
            adv_sensors = df.sensor_id.unique()
            adv_sensors_modbus_ids = df.id.unique()

            # extracting date from datetime
            df["date"] = pd.to_datetime(df["timestamp"].dt.date)

            # Reseting index
            df.sort_values(by=["timestamp"], ascending=True).reset_index(inplace=True)

            # grouping data by date-hour and sensor id
            adv_grp = df.groupby(
                by=[
                    df.timestamp.map(
                        lambda x: "%04d-%02d-%02d-%02d"
                        % (x.year, x.month, x.day, x.hour)
                    ),
                    "sensor_id",
                    "date",
                ]
            )

            # estimating hourly temperature mean values
            adv_grp_temp = adv_grp["temperature"].mean().reset_index()

            # binning temperature values
            adv_grp_temp["temp_bin"] = pd.cut(adv_grp_temp["temperature"], TEMP_BINS)

            # converting bins to str
            adv_grp_temp["temp_bin"] = adv_grp_temp["temp_bin"].astype(str)

            # get bin counts for each sensor-day combination
            adv_grp_date = adv_grp_temp.groupby(by=["sensor_id", "date", "temp_bin"])
            adv_cnt = adv_grp_date["temperature"].count().reset_index()
            adv_cnt.rename(columns={"temperature": "temp_cnt"}, inplace=True)

            json_data = []
            for adv_sensor_id in adv_sensors:

                adv_cnt_sensor = adv_cnt[adv_cnt["sensor_id"] == adv_sensor_id]

                del adv_cnt_sensor["sensor_id"]

                # Adding missing date/temp_bin combos
                bins_list, df_list = resample(adv_cnt_sensor, TEMP_BINS, dt_from, dt_to)

                bins_json = []

                for i, bin_range in enumerate(bins_list):
                    temp_bin_df = df_list[i]
                    temp_bin_df["date"] = pd.to_datetime(
                        temp_bin_df["date"], format="%Y-%m-%d"
                    ).dt.strftime("%Y-%m-%d")

                    bins_json.append(
                        '["'
                        + bin_range
                        + '",'
                        + temp_bin_df.to_json(orient="records")
                        + "]"
                    )

                json_data.append("[" + ",".join(bins_json) + "]")

            adv_sensors_temp["data"] = "[" + ",".join(json_data) + "]"

        else:
            adv_sensors_modbus_ids = []

        return render_template(
            template + ".html",
            num_adv_sensors=len(adv_sensors_modbus_ids),
            adv_sensors=adv_sensors_modbus_ids,
            adv_sensors_temp=adv_sensors_temp,
            dt_from=dt_from.strftime("%B %d, %Y"),
            dt_to=dt_to.strftime("%B %d, %Y"),
        )

    elif template == "electricity":
        energy_data = {}

        dt_from, dt_to = parse_date_range_argument(request.args.get("range"))

        # lights-on analysis
        lights_results_df = lights_energy_use(dt_from, dt_to)

        # ventilation analysis
        ventilation_results_df = ventilation_energy_use(dt_from, dt_to)

        # jsonify
        energy_data["data"] = (
            "["
            + lights_results_df.to_json(orient="records")
            + ","
            + ventilation_results_df.to_json(orient="records")
            + "]"
        )

        return render_template(
            template + ".html",
            energy_data=energy_data,
            dt_from=dt_from.strftime("%B %d, %Y"),
            dt_to=dt_to.strftime("%B %d, %Y"),
        )

    return render_template(template + ".html")
