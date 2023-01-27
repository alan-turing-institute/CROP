def main() -> None:
    from arima.data_access import get_training_data
    from arima.clean_data import clean_data
    import pickle
    import logging, coloredlogs
    import sys

    # set up logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    field_styles = coloredlogs.DEFAULT_FIELD_STYLES
    field_styles["levelname"][
        "color"
    ] = "white"  # change the default levelname color from black to white
    coloredlogs.ColoredFormatter(field_styles=field_styles)
    coloredlogs.install(level="INFO")

    env_raw, energy_raw = get_training_data(num_rows=500)

    with open("dump/env_raw.pkl", "wb") as handle:
        pickle.dump(env_raw, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open("dump/energy_raw.pkl", "wb") as handle:
        pickle.dump(energy_raw, handle, protocol=pickle.HIGHEST_PROTOCOL)

    env_clean, energy_clean = clean_data(env_raw, energy_raw)

    with open("dump/env_clean.pkl", "wb") as handle:
        pickle.dump(env_clean, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open("dump/energy_clean.pkl", "wb") as handle:
        pickle.dump(energy_clean, handle, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    main()
